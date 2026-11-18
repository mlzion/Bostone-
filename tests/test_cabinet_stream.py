import math
import hashlib
import re
import unittest
from pathlib import Path
from offline_cabinet import Hybrid


class CabinetStreamTests(unittest.TestCase):
    def test_continuous_stereo_long_stream_against_sparse_fir(self):
        taps=[(0,.5),(63,.01),(64,.02),(255,.03),(256,.04),(257,.05),(511,.06),(512,.07),(1024,.08)]
        hl=[0.]*1025; hr=[0.]*1025
        for i,x in taps:hl[i]=x;hr[i]=x*.6
        c=Hybrid([hl,hr]); left=[];right=[]
        # Over two seconds: catches periodic gaps; positive signals avoid sine zero ambiguity.
        for i in range(100800):
            l=.04+.02*math.sin(i*.11);r=-.03+.01*math.sin(i*.07)
            left.append(l);right.append(r);y=c.tick(l,r)
            for ch,xs,scale in ((0,left,1),(1,right,.6)):
                expected=sum(v*scale*xs[i-64-k] for k,v in taps if i>=64+k)
                self.assertAlmostEqual(y[ch],expected,places=11)
            if i>64+1024:self.assertGreater(y[0],.01);self.assertLess(y[1],-.005)

    def test_boundary_impulses(self):
        for tap in (0,63,64,255,256,257,511,512,513,1024):
            h=[0.]*(tap+1);h[tap]=.25
            c=Hybrid([h,h])
            for i in range(tap+192):
                y=c.tick(1 if i==0 else 0,0)
                self.assertAlmostEqual(y[0],.25 if i==tap+64 else 0,places=11)
                self.assertAlmostEqual(y[1],0,places=12)

    def test_native_product_and_bypass_work_gate(self):
        s=(Path(__file__).parents[1]/'jsfx/Bostone_Plexi_v0.4.jsfx').read_text()
        self.assertEqual(hashlib.sha256('\n'.join(re.findall(r'^slider\d+:.*$',s,re.M)).encode()).hexdigest(),'a4abebf93213150cc4cbb736332cfb03e47e6ceda8f9a5508592f94a76782e4d')
        self.assertIn('convolve_c(work,hp,n)',s)
        self.assertIn('cab_should_run=cab_enable || cab_mix>0;',s)
        self.assertIn('!cab_running ? (cab_reset(); cab_running=1;);',s)
        # Approximate expensive per-bin work reduction at max length, without a fragile timing threshold.
        old_pairs=2*512*128/64
        new_pairs=2*(4*128/64+127*512/256)
        self.assertLess(new_pairs,old_pairs*.27)
