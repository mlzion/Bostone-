import cmath
import hashlib
import math
import random
import re
import unittest
from pathlib import Path
from offline_dsp import coeff
from offline_v02 import V02
from offline_v021 import V021, V021_RANGES
from test_v02 import response

ROOT=Path(__file__).parents[1]
RATES=(44100,48000)


class V021Tests(unittest.TestCase):
    def test_production_delta_and_preserved_files(self):
        preserved={'Bostone_Preamp.jsfx':'442fee3dc5c81beb6f7269381dbf5b840d948d32',
                   'Bostone_Preamp_v0.2.jsfx':'d626e06b4d4a2eac3a85471d3d121b344c810092',
                   'Bostone_Plexi_v0.3.jsfx':'66d21f8843d78335bc3e178b50ff76cfcc2b2c6f'}
        for path,sha in preserved.items():
            b=((ROOT.parent/'Plexi/jsfx'/path) if 'Plexi' in path else (ROOT/'jsfx'/path)).read_bytes()
            self.assertEqual(hashlib.sha1(b'blob '+str(len(b)).encode()+b'\0'+b).hexdigest(),sha,path)
        old=(ROOT/'jsfx/Bostone_Preamp_v0.2.jsfx').read_text()
        new=(ROOT/'jsfx/Bostone_Preamp_v0.2.1.jsfx').read_text()
        expected=old
        for a,b in [('desc:Bostone Preamp v0.2','desc:Bostone Preamp v0.2.1'),
                    ('slider2:80<40,300,1>','slider2:80<40,1000,1>'),
                    ('slider4:400<150,1000,1>','slider4:400<150,2000,1>'),
                    ('slider5:10000<400,15000,1>','slider5:10000<400,10000,1>'),
                    ('bounded(slider2,40,300)','bounded(slider2,40,1000)'),
                    ('bounded(slider4,150,1000)','bounded(slider4,150,2000)'),
                    ('bounded(slider5,400,15000)','bounded(slider5,400,10000)')]:
            self.assertEqual(expected.count(a),1)
            expected=expected.replace(a,b)
        # Strong source contract: every other byte, including equations, states,
        # gains, slopes, bypasses and smoothing, must remain as in v0.2.
        self.assertEqual(new,expected)
        self.assertEqual(re.findall(r'^slider\d+:([^<]+)',old,re.M),re.findall(r'^slider\d+:([^<]+)',new,re.M))
        names=[p.read_text().splitlines()[0] for p in (ROOT/'jsfx').glob('*.jsfx')]
        self.assertEqual(len(names),len(set(names)))
        self.assertNotIn('pow(',new) # Original exp/log implementation; no new math API.

    def test_endpoints_reach_filter_targets_and_response(self):
        for sr in RATES:
            for key,index,kind,lo,hi in [('hp',0,'hp',40,1000),('pre_freq',1,'bell',150,2000),('lp',2,'lp',400,10000)]:
                m=V021(sr)
                for value in (lo,hi):
                    m.set(**{key:value},pre_gain=12)
                    gain=12 if kind=='bell' else 0
                    self.assertEqual(m.p[key],value)
                    self.assertEqual(m.filters[index].target,coeff(kind,value,gain,sr))
                    expected=10**(12/20) if kind=='bell' else 1/math.sqrt(2)
                    self.assertAlmostEqual(response(m.filters[index].target,value,sr),expected,places=8)
                m.set(**{key:hi+50000}); self.assertEqual(m.p[key],hi)
                self.assertEqual(m.filters[index].target,coeff(kind,hi,12 if kind=='bell' else 0,sr))
                m.set(**{key:lo-10000}); self.assertEqual(m.p[key],lo)
            # User's 800 Hz setting must not silently stop at v0.2's 300 Hz limit.
            m=V021(sr); m.set(hp=800)
            self.assertEqual(m.filters[0].target,coeff('hp',800,0,sr))

    def test_measured_low_frequency_removal(self):
        for sr in RATES:
            def rms(cut):
                m=V021(sr,hp=cut,dist=0,post=0,input=0,output=0)
                samples=[]
                for i in range(8000):
                    y=m.tick(.01*math.sin(2*math.pi*100*i/sr),0)[0]
                    if i>=4000:samples.append(y)
                return math.sqrt(sum(x*x for x in samples)/len(samples))
            self.assertGreater(20*math.log10(rms(40)/rms(1000)),30)
            self.assertLess(response(coeff('hp',800,0,sr),100,sr),response(coeff('hp',300,0,sr),100,sr)/5)
            self.assertGreater(response(coeff('bell',2000,12,sr),2000,sr),response(coeff('bell',1000,12,sr),2000,sr)*1.4)
            self.assertLess(response(coeff('lp',10000,0,sr),10000,sr),response(coeff('lp',15000,0,sr),10000,sr)*.8)

    def test_identical_processing_with_shared_settings_and_modes(self):
        for sr in RATES:
            for pre_mode,drive_mode in ((0,0),(1,0),(0,1),(1,1)):
                a,b=V02(sr,pre_mode=pre_mode,drive_mode=drive_mode),V021(sr,pre_mode=pre_mode,drive_mode=drive_mode)
                for i in range(2000):
                    if i==500:
                        p=dict(hp=218,pre_freq=685,pre_gain=6.4,lp=2000,drive=20,mid=5.1,mid_freq=717,low=-8.2,high=-12)
                        a.set(**p); b.set(**p)
                    if i==1500:a.set(pre=0,dist=0); b.set(pre=0,dist=0)
                    x=.1*math.sin(i*.13)
                    self.assertEqual(a.tick(x,-x),b.tick(x,-x))

    def test_filter_poles_impulses_and_extreme_automation(self):
        rng=random.Random(21)
        for sr in RATES:
            for hp,mid,lp in ((40,150,400),(1000,2000,400),(1000,150,10000),(800,800,400)):
                m=V021(sr,hp=hp,pre_freq=mid,pre_gain=12,lp=lp,dist=0,post=0)
                for f in m.filters:
                    a1,a2=f.c[3:]
                    self.assertLess(max(abs((-a1+s*cmath.sqrt(a1*a1-4*a2))/2) for s in (-1,1)),1)
                for i in range(6000):
                    y=m.tick(1 if i==0 else 0,0)
                    self.assertTrue(all(map(math.isfinite,y))); self.assertEqual(y[1],0)
                self.assertLess(abs(y[0]),.00001)
            m=V021(sr)
            self.assertEqual(m.tick(0,0),(0,0))
            for i in range(6000):
                if i%263==0:m.set(**{k:rng.choice(v) for k,v in V021_RANGES.items()},pre_mode=rng.randrange(2),drive_mode=rng.randrange(2))
                y=m.tick(.1*math.sin(i*.17),0)
                self.assertTrue(math.isfinite(y[0])); self.assertLess(abs(y[0]),100); self.assertEqual(y[1],0)
            for v in (math.nan,math.inf,-math.inf):self.assertTrue(all(map(math.isfinite,m.tick(v,v))))

    def test_new_endpoint_smoothing_and_bypass(self):
        for sr in RATES:
            for key,value in dict(hp=1000,pre_freq=2000,lp=400).items():
                m=V021(sr,pre_gain=12)
                prev=0;peak=0
                for i in range(4000):
                    if i==2000:m.set(**{key:value})
                    y=m.tick(.01*math.sin(2*math.pi*440*i/sr),0)[0]
                    if i>=2000:peak=max(peak,abs(y-prev))
                    prev=y
                self.assertLess(peak,.02,key)
            m=V021(sr,hp=1000,pre_freq=2000,lp=400,drive_mode=1)
            m.set(master=1)
            for _ in range(1000):m.tick(.2,-.3)
            self.assertEqual(m.tick(.2,-.3),(.2,-.3))
