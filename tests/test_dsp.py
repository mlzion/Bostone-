import cmath
import math
import random
import re
import unittest
from pathlib import Path
from offline_dsp import Model, coeff, DEFAULT, RANGES

RATES = (22050, 32000, 44100, 48000, 88200, 96000, 192000)

class DSPTests(unittest.TestCase):
    def test_silence(self):
        for sr in RATES:
            m = Model(sr)
            self.assertTrue(all(m.tick(0,0)==(0,0) for _ in range(2048)))

    def test_stereo_isolation_and_symmetry(self):
        for active in (0,1):
            m = Model()
            for i in range(4096):
                x = .2*math.sin(i*.13)
                frame = (x,0) if active==0 else (0,x)
                self.assertEqual(m.tick(*frame)[1-active],0)
        m = Model()
        for i in range(2048):
            y = m.tick(.1*math.sin(i*.17),.1*math.sin(i*.17))
            self.assertEqual(*y)

    def test_poles_and_frequency_response(self):
        for sr in RATES:
            for kind,frequencies in [('hp',(40,300)),('lp',(2000,15000)),
                                     ('bell',(150,400,1000,1200,4000)),('low',(150,)),('high',(4000,))]:
                for f in frequencies:
                    for gain in (-12,0,12):
                        b0,b1,b2,a1,a2 = coeff(kind,f,gain,sr)
                        poles = ((-a1+cmath.sqrt(a1*a1-4*a2))/2,(-a1-cmath.sqrt(a1*a1-4*a2))/2)
                        self.assertLess(max(map(abs,poles)),1)
                        def response(w):
                            z=cmath.exp(-1j*w)
                            return abs((b0+b1*z+b2*z*z)/(1+a1*z+a2*z*z))
                        if kind=='hp':
                            self.assertAlmostEqual(response(0),0,places=8)
                        if kind=='lp':
                            self.assertAlmostEqual(response(math.pi),0,places=8)
                        if kind=='bell':
                            self.assertAlmostEqual(response(2*math.pi*min(f,.45*sr)/sr),10**(gain/20),places=7)
                        if kind=='low':
                            self.assertAlmostEqual(response(0),10**(gain/20),places=7)
                        if kind=='high':
                            self.assertAlmostEqual(response(math.pi),10**(gain/20),places=7)

    def test_gain_and_all_section_bypasses(self):
        for input_db,output_db in ((0,-6),(-24,12),(24,-24)):
            m=Model(pre=0,dist=0,post=0,input_db=input_db,output_db=output_db)
            expected=.01*10**((input_db+output_db)/20)
            self.assertAlmostEqual(m.tick(.01,-.01)[0],expected,places=12)
        m=Model(pre=0,dist=0,post=0,input=0,output=0,input_db=24,output_db=12)
        self.assertEqual(m.tick(.23,-.47),(.23,-.47))
        for section in ('pre','dist','post'):
            settings=dict(pre=0,dist=0,post=0,input=0,output=0)
            m=Model(**settings, low=6, mid=-6, high=6)
            self.assertEqual(m.tick(.17,-.2),(.17,-.2))
            m.set(**{section:1})
            ys=[m.tick(.17,-.2) for _ in range(4000)]
            self.assertGreater(abs(ys[-1][0]-.17),1e-5)
            m.set(**{section:0})
            for _ in range(1000): m.tick(.17,-.2)
            self.assertEqual(m.tick(.17,-.2),(.17,-.2))

    def test_drive_transfer(self):
        for d in (1,3,20):
            m=Model(pre=0,post=0,input=0,output=0,drive=d)
            for x in (-10,-.2,0,.2,10):
                self.assertAlmostEqual(m.tick(x,-x)[0],math.tanh(d*x),places=12)

    def test_master_bypass(self):
        m=Model()
        m.set(master=1)
        for _ in range(1000): m.tick(.3,-.2)
        for x in (0,.01,-.7,3): self.assertEqual(m.tick(x,-x),(x,-x))

    def test_finite_under_automation_and_extremes(self):
        rng=random.Random(2718)
        for sr in RATES:
            m=Model(sr)
            peak=0
            for i in range(12000):
                if i%257==0:
                    m.set(**{k:rng.choice(v) for k,v in RANGES.items()})
                x=1 if i==0 else .3*math.sin(2*math.pi*997*i/sr)
                y=m.tick(x,-x)
                self.assertTrue(all(math.isfinite(v) for v in y))
                peak=max(peak,*map(abs,y))
            self.assertLess(peak,100) # Loose containment bound, not an output limiter.
            for x in (math.nan,math.inf,-math.inf,1e30):
                self.assertTrue(all(map(math.isfinite,m.tick(x,x))))

    def test_parameter_discontinuities(self):
        # Low-level continuous sine; controls move at a zero-crossing-independent point.
        for control,value in dict(input_db=24,output_db=12,drive=20,hp=300,lp=2000,
                                  pre_gain=12,pre_freq=1000,low=12,mid=12,
                                  mid_freq=4000,high=12,pre=0,dist=0,post=0,
                                  master=1,input=0,output=0).items():
            m=Model()
            previous=0.; jump=0.
            for i in range(6000):
                if i==3000: m.set(**{control:value})
                y=m.tick(.01*math.sin(2*math.pi*440*i/48000),0)[0]
                if i>=3000: jump=max(jump,abs(y-previous))
                previous=y
            self.assertLess(jump,.02,control)

    def test_source_contract(self):
        source=(Path(__file__).parents[1]/'jsfx/Bostone_Preamp.jsfx').read_text()
        for fragment in ('0.020*srate','0.010*srate','0.45*srate','a=s/2;',
                         'post_low.target(3,150','post_high.target(4,4000',
                         'function tanh(x)','x1l,x2l,y1l,y2l,x1r,x2r,y1r,y2r'):
            self.assertIn(fragment,source)
        sliders = re.findall(r'^slider(\d+):([^<]+)<([^>]+)>',source,re.M)
        self.assertEqual(len(sliders),17)
        keys = ('input_db','hp','pre_gain','pre_freq','lp','pre','drive','dist',
                'low','mid','mid_freq','high','post','output_db','master','input','output')
        for (_,default,limits), key in zip(sliders,keys):
            self.assertEqual(float(default),DEFAULT[key])
            if key in RANGES:
                self.assertEqual(tuple(map(float,limits.split(',')[:2])),RANGES[key])
        # EEL2 identifiers are case-insensitive: a and A must never coexist.
        for declaration in re.findall(r'(?:local|instance)\(([^)]*)\)',source):
            names = [n.strip().lower() for n in declaration.split(',')]
            self.assertEqual(len(names),len(set(names)),declaration)

if __name__=='__main__': unittest.main()
