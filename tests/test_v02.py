import cmath
import hashlib
import math
import random
import re
import unittest
from pathlib import Path
from offline_dsp import Model, coeff
from offline_v02 import V02, band_coeff, EXTRA, V02_RANGES

ROOT=Path(__file__).parents[1]
RATES=(44100,48000,96000)


def response(c,f,sr):
    b0,b1,b2,a1,a2=c
    z=cmath.exp(-2j*math.pi*f/sr)
    return abs((b0+b1*z+b2*z*z)/(1+a1*z+a2*z*z))


class V02Tests(unittest.TestCase):
    def test_v01_file_identity_and_slider_contract(self):
        old=(ROOT/'jsfx/Bostone_Preamp.jsfx').read_bytes()
        # Blob SHA of merged v0.1: prevents accidental edits to the old plugin.
        self.assertEqual(hashlib.sha1(b'blob '+str(len(old)).encode()+b'\0'+old).hexdigest(),
                         '442fee3dc5c81beb6f7269381dbf5b840d948d32')
        new=(ROOT/'jsfx/Bostone_Preamp_v0.2.jsfx').read_text()
        a=re.findall(r'^slider\d+:.*$',old.decode(),re.M)
        b=re.findall(r'^slider\d+:.*$',new,re.M)
        self.assertEqual(b[:17], [x.replace('<2000,15000,1>','<400,15000,1>') for x in a])
        self.assertEqual(len(b),25)
        self.assertIn('desc:Bostone Preamp v0.2',new)
        self.assertIn('pre_lp.target(1,bounded(slider5,400,15000),0);',new)
        # Original biquad definitions stay identical in the new production file.
        for name in ('target','snap','smooth','clear','left','right'):
            pattern=rf'^function {name}\([\s\S]*?^\);'
            self.assertEqual(re.search(pattern,old.decode(),re.M)[0],
                             re.search(pattern,new,re.M)[0],name)
        for n,k in enumerate(EXTRA,18):
            default=float(re.search(rf'^slider{n}:([^<]+)',new,re.M)[1])
            self.assertEqual(default,EXTRA[k])

    def test_legacy_exact_model_equivalence_with_automation(self):
        for sr in RATES:
            a,b=Model(sr),V02(sr)
            rng=random.Random(2)
            for i in range(5000):
                if i==1000: b.set(bp_freq=4000,bp_q=4,bp_level=12,stage_db=18,intercut=800,trim_db=12)
                if i==1500:
                    p=dict(hp=218,pre_gain=6.4,pre_freq=685,lp=2000,drive=20,
                           low=-8.2,mid=5.1,mid_freq=717,high=-12,output_db=-2.6)
                    a.set(**p); b.set(**p)
                if i==3000: a.set(pre=0,dist=0,post=0); b.set(pre=0,dist=0,post=0)
                if i==4000: a.set(master=1); b.set(master=1)
                x,y=rng.uniform(-.2,.2),rng.uniform(-.2,.2)
                self.assertEqual(a.tick(x,y),b.tick(x,y))

    def test_v01_response_cutoffs_and_slopes(self):
        for sr in RATES:
            for kind,fc in [('hp',80),('lp',10000),('lp',400)]:
                c=coeff(kind,fc,0,sr)
                self.assertAlmostEqual(response(c,fc,sr),1/math.sqrt(2),places=9)
            hp=coeff('hp',80,0,sr)
            slope=20*math.log10(response(hp,2,sr)/response(hp,1,sr))
            self.assertAlmostEqual(slope,12.0412,places=3)
            lp=coeff('lp',400,0,sr)
            # Compare along bilinear-warped frequency to isolate prototype slope.
            f1=sr/math.pi*math.atan(10*math.tan(math.pi*400/sr))
            f2=sr/math.pi*math.atan(20*math.tan(math.pi*400/sr))
            self.assertAlmostEqual(20*math.log10(response(lp,f2,sr)/response(lp,f1,sr)),-12.041,places=2)
            chain=response(coeff('hp',218,0,sr),685,sr)*response(coeff('bell',685,6.4,sr),685,sr)*response(coeff('lp',2000,0,sr),685,sr)
            self.assertLess(chain,10**(6.4/20)) # Cuts are not ideal passband edges.

    def test_band_response_and_poles(self):
        for sr in RATES:
            for fc in (150,685,4000):
                for q in (.25,1,4):
                    c=band_coeff(fc,q,sr)
                    self.assertAlmostEqual(response(c,fc,sr),1,places=10)
                    for sign in (-1,1):
                        t=math.tan(math.pi*fc/sr)*(math.sqrt(1+1/(4*q*q))+sign/(2*q))
                        edge=sr/math.pi*math.atan(t)
                        self.assertAlmostEqual(response(c,edge,sr),1/math.sqrt(2),places=9)
                    self.assertAlmostEqual(response(c,0,sr),0)
                    self.assertAlmostEqual(response(c,sr/2,sr),0)
                    a1,a2=c[3:]
                    self.assertLess(max(abs((-a1+s*cmath.sqrt(a1*a1-4*a2))/2) for s in (-1,1)),1)

    def test_band_alternative_and_center_level(self):
        a=V02(pre_mode=1,dist=0,post=0,input=0,output=0)
        b=V02(pre_mode=1,dist=0,post=0,input=0,output=0,hp=300,lp=400,pre_gain=12,pre_freq=1000,bp_level=6)
        gain=10**(6/20)
        for i in range(3000):
            x=.01*math.sin(i*.1)
            self.assertAlmostEqual(b.tick(x,0)[0],a.tick(x,0)[0]*gain,places=12)

    def test_silence_isolation_finite_and_automation(self):
        rng=random.Random(23)
        for sr in (22050,32000,44100,48000,88200,96000,192000):
            m=V02(sr,pre_mode=1,drive_mode=1)
            self.assertEqual(m.tick(0,0),(0,0))
            for i in range(6000):
                if i%251==0:
                    m.set(**{k:rng.choice(v) for k,v in V02_RANGES.items()},pre_mode=rng.randrange(2),drive_mode=rng.randrange(2))
                y=m.tick(.05*math.sin(i*.14),0)
                self.assertEqual(y[1],0)
                self.assertTrue(math.isfinite(y[0]))
                self.assertLess(abs(y[0]),100)
            for v in (math.nan,math.inf,-math.inf):
                self.assertTrue(all(map(math.isfinite,m.tick(v,v))))

    def test_low_cutoff_near_bell_and_decay(self):
        for sr in RATES:
            for bell in (150,400,685,1000):
                m=V02(sr,lp=400,pre_gain=12,pre_freq=bell,dist=0,post=0)
                peak=0
                for i in range(12000):
                    y=m.tick(1 if i==0 else 0,0)[0]
                    self.assertTrue(math.isfinite(y)); peak=max(peak,abs(y))
                self.assertLess(peak,2)
                self.assertLess(abs(y),.000001)

    def test_stronger_drive_measured_difference(self):
        legacy=V02(pre=0,post=0,input=0,output=0,drive=10)
        strong=V02(pre=0,post=0,input=0,output=0,drive=10,drive_mode=1)
        a=[];b=[]
        for i in range(4800):
            x=.1*math.sin(2*math.pi*500*i/48000)
            ya=legacy.tick(x,0)[0]; yb=strong.tick(x,0)[0]
            if i>=2400: a.append(ya); b.append(yb)
        def harmonic(v,k):
            return abs(sum(x*cmath.exp(-2j*math.pi*500*k*i/48000) for i,x in enumerate(v)))
        # Level-invariant third/fundamental ratio: verifies added compression.
        self.assertGreater(harmonic(b,3)/harmonic(b,1),harmonic(a,3)/harmonic(a,1)*1.5)
        self.assertGreater(harmonic(b,1),1) # Fundamental/note pitch remains present.

    def test_bypass_and_new_control_ramps(self):
        for control,value in dict(pre_mode=1,drive_mode=1,bp_freq=4000,bp_q=4,bp_level=12,
                                  stage_db=18,intercut=800,trim_db=12,lp=400).items():
            m=V02(pre_mode=1 if control.startswith('bp_') else 0,drive_mode=1 if control in ('stage_db','intercut','trim_db') else 0)
            prev=0;peak=0
            for i in range(4000):
                if i==2000: m.set(**{control:value})
                y=m.tick(.01*math.sin(2*math.pi*440*i/48000),0)[0]
                if i>=2000: peak=max(peak,abs(y-prev))
                prev=y
            self.assertLess(peak,.02,control)
        m=V02(pre_mode=1,drive_mode=1)
        m.set(master=1)
        for _ in range(1000): m.tick(.17,-.29)
        self.assertEqual(m.tick(.17,-.29),(.17,-.29))
        m.set(master=0,pre=0,dist=0,post=0,input=0,output=0)
        for _ in range(1000): m.tick(.17,-.29)
        self.assertEqual(m.tick(.17,-.29),(.17,-.29))
