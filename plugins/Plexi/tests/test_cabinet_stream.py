import math
import hashlib
import re
import unittest
from pathlib import Path
from offline_cabinet import Partitioned as LiveCabinet


class CabinetStreamTests(unittest.TestCase):
    def test_continuous_stereo_long_stream_against_sparse_fir(self):
        taps=[(0,.5),(63,.01),(64,.02),(255,.03),(256,.04),(257,.05),(511,.06),(512,.07),(1024,.08)]
        hl=[0.]*1025; hr=[0.]*1025
        for i,x in taps:hl[i]=x;hr[i]=x*.6
        c=LiveCabinet([hl,hr]); left=[];right=[]
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
            c=LiveCabinet([h,h])
            for i in range(tap+192):
                y=c.tick(1 if i==0 else 0,0)
                self.assertAlmostEqual(y[0],.25 if i==tap+64 else 0,places=11)
                self.assertAlmostEqual(y[1],0,places=12)

    def test_native_product_and_bypass_work_gate(self):
        s=(Path(__file__).parents[1]/'jsfx/Bostone_Plexi_v0.4.jsfx').read_text()
        self.assertEqual(hashlib.sha256('\n'.join(re.findall(r'^slider\d+:.*$',s,re.M)).encode()).hexdigest(),'a4abebf93213150cc4cbb736332cfb03e47e6ceda8f9a5508592f94a76782e4d')
        self.assertIn('convolve_c(work+2,hp+2,62)',s)
        self.assertIn('work[0]*=hp[0]; work[1]*=hp[1];',s)
        self.assertIn('output[i]=acc[i]/512+overlap[i]',s)
        self.assertNotIn('cab_tail_parts',s)
        self.assertIn('want>4096',s)
        self.assertIn('cab_should_run=cab_enable || cab_mix>0;',s)
        self.assertIn('!cab_running ? (cab_reset(); cab_running=1;);',s)
        # Worst callback: <=64 partitions * 128 real slots * 2 channels,
        # versus old 127 tail partitions * 1024 slots * 2 plus head work.
        self.assertLess(64*128*2,127*1024*2/15)

    def test_same_file_restore_does_not_request_reload(self):
        s=(Path(__file__).parents[1]/'jsfx/Bostone_Plexi_v0.4.jsfx').read_text()
        serial=s.split('@serialize',1)[1].split('@gfx',1)[0]
        self.assertLess(serial.index('cab_serial_read=file_avail(0)>=0'),serial.index('file_var('))
        self.assertIn('cab_serial_read ? cab_restore_selection();',serial)
        fn=s.split('function cab_restore_selection()',1)[1].split('function cab_reset()',1)[0]
        self.assertIn('strcmp(#cab_file,#cab_prior_restore)!==0 ? cab_reload=1;',fn)
