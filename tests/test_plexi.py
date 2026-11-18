import hashlib
import itertools
import math
import random
import re
import unittest
from pathlib import Path
from offline_plexi import Plexi, Tone, tone_matrix, solve_complex, triode, current, LIMITS, DEFAULT

ROOT=Path(__file__).parents[1]
RATES=(44100,48000,88200,96000,176400,192000,384000)


class PlexiTests(unittest.TestCase):
    def test_source_and_preserved_baseline(self):
        old=(ROOT/'jsfx/Bostone_Preamp.jsfx').read_bytes()
        self.assertEqual(hashlib.sha1(b'blob '+str(len(old)).encode()+b'\0'+old).hexdigest(),'442fee3dc5c81beb6f7269381dbf5b840d948d32')
        s=(ROOT/'jsfx/Bostone_Plexi_v0.3.jsfx').read_text()
        self.assertEqual(re.findall(r'^@\w+',s,re.M),['@init','@slider','@sample'])
        self.assertEqual(s.splitlines()[0],'desc:Bostone Plexi v0.3')
        sliders=re.findall(r'^slider(\d+):([^<]+)<([^>]+)>',s,re.M)
        self.assertEqual(len(sliders),10)
        for (_,default,limits),k in zip(sliders,DEFAULT):
            self.assertEqual(float(default),DEFAULT[k])
            self.assertEqual(tuple(map(float,limits.split(',')[:2])),LIMITS[k])
        for token in ('ct_g=2*srate*0.0000000005','220000','33000','2000000','lchan.amp','rchan.amp','enable_g === 0'):
            self.assertIn(token,s)
        self.assertNotIn('ext_noinit',s)
        self.assertNotIn('import ',s)

    def test_silence_and_stereo(self):
        for sr in RATES:
            m=Plexi(sr)
            self.assertTrue(all(m.tick(0,0)==(0,0) for _ in range(256)))
        for active in (0,1):
            m=Plexi()
            for i in range(3000):
                x=.1*math.sin(i*.1)
                y=m.tick(x,0) if active==0 else m.tick(0,x)
                self.assertEqual(y[1-active],0)
        m=Plexi()
        for i in range(200):
            l,r=m.tick(.2,.2); self.assertEqual(l,r)

    def test_level_bounds_and_invalid_inputs(self):
        for sr in RATES:
            m=Plexi(sr,input_db=24,pre_db=36,power_db=24,output_db=0,presence=10)
            for i in range(3000):
                y=m.tick(16*math.sin(i*.31),-16*math.sin(i*.23))
                self.assertTrue(all(math.isfinite(v) and abs(v)<=.800000000001 for v in y))
            for v in (math.nan,math.inf,-math.inf,1e300,-1e300):
                self.assertTrue(all(math.isfinite(x) and abs(x)<=.800000000001 for x in m.tick(v,v)))

    def test_pot_corners_impulse_and_decay(self):
        for sr in (44100,96000,384000):
            for b,m,t in itertools.product((0,1),repeat=3):
                tone=Tone(sr,b,m,t)
                last=0
                for i in range(4000):
                    last=tone.tick(1 if i==0 else 0,0)
                    self.assertTrue(math.isfinite(last)); self.assertLess(abs(last),1.01)
                self.assertLess(abs(last),.001)
        m=Plexi()
        for i in range(16000):
            y=m.tick(1 if i==0 else 0,0)[0]
            self.assertTrue(math.isfinite(y))
        self.assertLess(abs(y),.00001)

    def test_passive_network_ac_and_interactions(self):
        for b,m,t in itertools.product((0,.5,1),repeat=3):
            for f in (30,100,500,2000,10000):
                a,g=tone_matrix(48000,b,m,t,complex_frequency=f)
                h=solve_complex(a,[1/33000,g[0],0,0,0])[-1]
                self.assertLessEqual(abs(h),1.000001)
        def h(m,t,f):
            a,g=tone_matrix(48000,.5,m,t,complex_frequency=f)
            return abs(solve_complex(a,[1/33000,g[0],0,0,0])[-1])
        # Treble's effect depends on Middle: cannot factor into unrelated EQ bands.
        self.assertGreater(abs(h(.2,.8,1000)/h(.2,.2,1000)-h(.8,.8,1000)/h(.8,.2,1000)),.05)
        # Time-domain capacitor companions agree with independent analog nodal solve
        # at the bilinear-warped frequency, not a cloned coefficient calculation.
        sr=48000; f=1000; tone=Tone(sr)
        ys=[]; xs=[]
        for i in range(12000):
            x=math.sin(2*math.pi*f*i/sr); y=tone.tick(x,0)
            if i>=9600: ys.append(y); xs.append(x)
        gain=math.sqrt(sum(y*y for y in ys)/sum(x*x for x in xs))
        warped=sr/math.pi*math.tan(math.pi*f/sr)
        a,g=tone_matrix(sr,.5,.5,.5,complex_frequency=warped)
        expected=abs(solve_complex(a,[1/33000,g[0],0,0,0])[-1])
        self.assertAlmostEqual(gain,expected,places=6)

    def test_bypass_exact_and_state_warmth(self):
        a=Plexi(); b=Plexi(enable=0)
        for i in range(2000):
            x=.2*math.sin(i*.17)
            a.tick(x,-x)
            self.assertEqual(b.tick(x,-x),(x,-x))
        # Bypassed processing has identical states; no stale capacitor histories.
        self.assertEqual(a.state,b.state); self.assertEqual(a.tone.h,b.tone.h)
        b.set(enable=1)
        for i in range(1000):
            y=a.tick(.1,-.2); z=b.tick(.1,-.2)
        self.assertEqual(y,z)
        b.set(enable=0)
        for _ in range(1000):b.tick(.1,-.2)
        self.assertEqual(b.tick(1e300,-1e300),(1e300,-1e300))

    def test_extreme_controls_and_transition_bounds(self):
        rng=random.Random(1959); m=Plexi()
        for i in range(6000):
            if i%701==0:m.set(**{k:rng.choice(v) for k,v in LIMITS.items() if k!='enable'})
            self.assertTrue(all(math.isfinite(x) for x in m.tick(.1*math.sin(i*.13),.2*math.sin(i*.17))))
        for k,(lo,hi) in LIMITS.items():
            m=Plexi(); prev=0; peak=0
            for i in range(3000):
                if i==1500:m.set(**{k:hi if DEFAULT[k]!=hi else lo})
                y=m.tick(.00001*math.sin(2*math.pi*440*i/48000),0)[0]
                if i>=1500:peak=max(peak,abs(y-prev))
                prev=y
            self.assertLess(peak,.02,k)
        # Isolate the first parameter-induced step from a clipped waveform's
        # ordinary derivative by comparing identical warmed instances.
        for k,(lo,hi) in LIMITS.items():
            a,b=Plexi(),Plexi()
            for i in range(500):
                x=.05*math.sin(i*.1); a.tick(x,0); b.tick(x,0)
            b.set(**{k:hi if DEFAULT[k]!=hi else lo})
            self.assertLess(abs(a.tick(.03,0)[0]-b.tick(.03,0)[0]),.002,k)

    def test_drive_curves_and_dc(self):
        self.assertAlmostEqual(triode(0,.22),0)
        self.assertGreater(abs(triode(.6,.22)+triode(-.6,.22)),.05)
        self.assertGreater(current(3),current(0)); self.assertLess(current(100000),1)
        m=Plexi(pre_db=36,power_db=24)
        acc=[]
        for i in range(18000):
            y=m.tick(.1*math.sin(2*math.pi*200*i/48000),0)[0]
            if i>=15600:acc.append(y)
        self.assertLess(abs(sum(acc)/len(acc)),.003)

    def test_rates_and_reinitialization(self):
        values=[]
        for sr in RATES:
            # Reconstructing at a new rate models JSFX @init reset, not host OS.
            m=Plexi(sr)
            samples=[]
            for i in range(int(.04*sr)):
                y=m.tick(.001*math.sin(2*math.pi*500*i/sr),0)[0]
                self.assertTrue(math.isfinite(y))
                if i>int(.02*sr):samples.append(y)
            values.append(math.sqrt(sum(y*y for y in samples)/len(samples)))
            self.assertEqual(Plexi(sr).tick(0,0),(0,0))
        self.assertLess(max(values)/min(values),1.2)
