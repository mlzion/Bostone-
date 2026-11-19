"""Source contracts and independently derived multirate FIR checks."""
import cmath
import hashlib
import math
import json
import random
from pathlib import Path
import re
import unittest

ROOT=Path(__file__).parents[1]


def coefficients(source):
    h=[0.]*65
    for i,v in re.findall(r'os_coef\[(\d+)\]=([-\d.]+);',source):h[int(i)]=float(v)
    return h


def convolve(x,h):
    y=[0.]*(len(x)+len(h)-1)
    for i,a in enumerate(x):
        for k,b in enumerate(h):y[i+k]+=a*b
    return y


def roundtrip(x,h,mode):
    if mode==0:return x
    up=[0.]*(2*len(x))
    up[::2]=[2*v for v in x]
    up=convolve(up,h)
    middle=roundtrip(up,h,mode-1)
    return convolve(middle,h)[::2]


class OversamplingTests(unittest.TestCase):
    def setUp(self):
        self.old=(ROOT/'jsfx/Bostone_Plexi_v0.4.jsfx').read_text()
        self.new=(ROOT/'jsfx/Bostone_Plexi_v0.5.jsfx').read_text()

    def test_frozen_versions_controls_and_cabinet(self):
        for name,sha in [('Bostone_Plexi_v0.3.jsfx','66d21f8843d78335bc3e178b50ff76cfcc2b2c6f'),('Bostone_Plexi_v0.4.jsfx','15c49083f48e97e18a659604b7661591e038642d')]:
            b=(ROOT/'jsfx'/name).read_bytes();self.assertEqual(hashlib.sha1(b'blob '+str(len(b)).encode()+b'\0'+b).hexdigest(),sha)
        self.assertEqual(re.findall(r'^slider.*',self.old,re.M),re.findall(r'^slider.*',self.new,re.M)[:19])
        def section(s,a,b):return s[s.index(a):s.index(b,s.index(a))]
        self.assertEqual(section(self.old,'function amp(x)','// CABINET FUNCTIONS'),section(self.new,'function amp(x)','// OVERSAMPLING:'))
        self.assertEqual(section(self.old,'function cab_pick()','// END CABINET FUNCTIONS'),section(self.new,'function cab_pick()','// END CABINET FUNCTIONS'))
        self.assertEqual(self.old[self.old.index('cab_in_l=spl0;'):],self.new[self.new.index('cab_in_l=spl0;'):])
        for s in (self.old,self.new):self.assertIn('want>4096',s)

    def test_filter_response_symmetry_and_gain(self):
        h=coefficients(self.new)
        self.assertAlmostEqual(sum(h),1,places=13)
        self.assertLess(max(abs(a-b) for a,b in zip(h,reversed(h))),1e-15)
        for i in range(0,65,2):
            if i!=32:self.assertEqual(h[i],0)
        def response(f):return abs(sum(v*cmath.exp(-2j*math.pi*f*i) for i,v in enumerate(h)))
        self.assertLess(abs(response(.2)-1),.001)
        self.assertLess(response(.3),.0002)
        self.assertLess(response(.5),.00001)

    def test_roundtrip_delay_and_unity(self):
        h=coefficients(self.new)
        for mode,delay in ((1,32),(2,48)):
            y=roundtrip([1.]+[0.]*128,h,mode)
            self.assertEqual(max(range(len(y)),key=lambda i:abs(y[i])),delay)
            self.assertAlmostEqual(sum(y),1,places=7)

    def test_host_cabinet_rate_and_fixed_latency(self):
        self.assertIn('amp_rate=srate*pow(2,mode)',self.new)
        self.assertIn('ct_g=2*amp_rate*',self.new)
        self.assertIn('0.150*amp_rate',self.new)
        self.assertEqual(self.new.count('pdc_delay=112;'),2)
        self.assertIn('new_length=bound(slider18,0,500)',self.new)
        self.assertIn("ch='rqsr'; rate=srate",self.new)
        self.assertNotIn('srate=',self.new)

    def test_mode_transition_and_memory(self):
        self.assertIn('os_mix=max(0,os_mix-ramp)',self.new)
        self.assertIn('os_config(os_requested); os_prime=256',self.new)
        self.assertIn('os_blend=enable_g*os_mix',self.new)
        # Derive regions from actual production call sites, not a shadow map.
        fir_bases=set(map(int,re.findall(r'\.os_(?:fir|up|store)\([^,]+,(\d+)\)',self.new)))
        self.assertEqual(len(fir_bases),8)
        coef=int(re.search(r'os_coef=(\d+);',self.new)[1])
        dry_bases=set(map(int,re.findall(r'(\d+)\[os_dpos\]',self.new)))
        pad_bases=set(map(int,re.findall(r'os_pad\(os_tick\(dry_[lr],[01]\),(\d+),',self.new)))
        self.assertEqual(len(dry_bases),2);self.assertEqual(len(pad_bases),2)
        regions=sorted([(coef,coef+65)]+[(n,n+65) for n in fir_bases]+[(n,n+48) for n in dry_bases|pad_bases])
        for a,b in regions:self.assertGreaterEqual(a,2048);self.assertLessEqual(b,65536)
        for (a,b),(c,d) in zip(regions,regions[1:]):self.assertLessEqual(b,c)
        self.assertIn('memset(4096,0,520)',self.new)
        self.assertIn('memset(4800,0,96)',self.new)

    def test_polyphase_matches_zero_stuffed_interpolation(self):
        h=coefficients(self.new);rng=random.Random(505)
        x=[rng.uniform(-1,1) for _ in range(200)]
        up=[0.]*(2*len(x));up[::2]=[2*v for v in x]
        expected=convolve(up,h)
        history=[0.]*33;p=0
        for n,v in enumerate(x):
            history[p]=v
            even=2*h[32]*history[(p-16)%33]
            odd=sum(2*h[2*j+1]*(history[(p-j)%33]+history[(p-31+j)%33]) for j in range(16))
            self.assertAlmostEqual(even,expected[2*n],places=13)
            self.assertAlmostEqual(odd,expected[2*n+1],places=13)
            p=(p+1)%33

    def test_recorded_host_spectrum_regression(self):
        folder=ROOT/'docs/measurements'
        baseline=json.loads((folder/'v0.4-baseline.json').read_text())
        measured=json.loads((folder/'v0.5-spectra.json').read_text())
        for old in baseline:
            cases=[v for v in measured if v['rate']==old['rate']]
            self.assertEqual(len(cases),3)
            for v in cases:
                self.assertLess(v['peak'],.23)
                if v['mode']==0:
                    self.assertEqual(v['measurements'],old['measurements'])
                else:
                    # High-frequency/high-input folded spectral energy is lower;
                    # this is measured data validation, not re-execution of REAPER.
                    improvement=old['measurements'][-1]['nonharmonic_db']-v['measurements'][-1]['nonharmonic_db']
                    self.assertGreater(improvement,5 if v['mode']==1 else 10)
                    for a,b in zip(v['measurements'][:5],old['measurements'][:5]):
                        self.assertLess(abs(20*math.log10(a['fundamental_amplitude']/b['fundamental_amplitude'])),2)
