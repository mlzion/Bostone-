import hashlib
import math
import random
import re
import tempfile
import unittest
import wave
from pathlib import Path
from offline_cabinet import B,MAX_FRAMES,Partitioned,PostMix,prepare,read_wav,direct
from offline_plexi import Plexi

ROOT=Path(__file__).parents[1]


class CabinetTests(unittest.TestCase):
    def test_preserved_amp_source_and_structure(self):
        old=(ROOT/'jsfx/Bostone_Plexi_v0.3.jsfx').read_text()
        new=(ROOT/'jsfx/Bostone_Plexi_v0.4.jsfx').read_text()
        self.assertEqual(new.split('function finite',1)[1].split('// CABINET FUNCTIONS:',1)[0],old.split('function finite',1)[1].split('pre_zero=',1)[0])
        for sec,end in (('@slider','@sample'),('@sample',None)):
            original=old.split('\n'+sec+'\n',1)[1]
            if end:original=original.split('\n'+end,1)[0]
            self.assertIn(original,new)
        self.assertEqual(re.findall(r'^slider(?:[1-9]|10):.*$',old,re.M),re.findall(r'^slider(?:[1-9]|10):.*$',new,re.M))
        b=old.encode(); self.assertEqual(hashlib.sha1(b'blob '+str(len(b)).encode()+b'\0'+b).hexdigest(),'66d21f8843d78335bc3e178b50ff76cfcc2b2c6f')
        for literal in ('@serialize','file_string(0,#cab_file)','@block','pdc_delay=64','fft_permute','fft_ipermute','/128',"ch='rqsr'",'want>32768','cab_fade_request=cab_reload && play_state===0','file_avail(0)>=0','slider19:/BostoneIR:None'):
            self.assertIn(literal,new)
        # Every transform is 128 complex pairs; bases/stride are 256 aligned.
        for base in (65536,196608,327680,458752):
            for p in range(512):self.assertEqual((base+p*256)//65536,(base+p*256+255)//65536)
        self.assertLess(655360+65536,8388608)
        self.assertNotIn('cab_restored=0',new.split('@init',1)[1].split('@slider',1)[0])

    def test_impulse_timing_gain_and_partition_boundaries(self):
        for n in (1,63,64,65,127,128,129,513):
            h=[0.]*n; h[0]=.7; h[-1]+=.13
            engine=Partitioned([h,h]); out=[engine.tick(1 if i==0 else 0,0) for i in range(n+2*B)]
            for i,y in enumerate(out):
                self.assertAlmostEqual(y[0],h[i-B] if B<=i<B+n else 0,places=11)
                self.assertAlmostEqual(y[1],0,places=12)
        h=[0.]*100; h[37]=.25
        engine=Partitioned([h,h]); out=[engine.tick(i==0,0)[0] for i in range(220)]
        self.assertAlmostEqual(out[B+37],.25,places=12)
        self.assertTrue(all(abs(x)<1e-12 for x in out[:B+37]))

    def test_stereo_against_direct_convolution(self):
        rng=random.Random(4)
        xs=[[rng.uniform(-.2,.2) for _ in range(320)] for _ in range(2)]
        hs=[[rng.uniform(-.02,.02) for _ in range(257)] for _ in range(2)]
        expected=[direct(x,h) for x,h in zip(xs,hs)]
        engine=Partitioned(hs)
        for i in range(len(expected[0])+B):
            y=engine.tick(*[x[i] if i<len(x) else 0 for x in xs])
            for ch in range(2):self.assertAlmostEqual(y[ch],expected[ch][i-B] if i>=B else 0,places=11)

    def test_modes_linked_stereo_gain_and_mix(self):
        h=[[.25,-.125],[.5,0]]
        raw=prepare(h,48000,48000); fixed=prepare(h,48000,48000,1); peak=prepare(h,48000,48000,2); norm18=prepare(h,48000,48000,3)
        self.assertEqual(raw,h)
        self.assertAlmostEqual(fixed[0][0],.25*10**(-18/20))
        self.assertEqual(peak[0][0],.5); self.assertEqual(peak[1][0],1)
        self.assertAlmostEqual(norm18[1][0],10**(-18/20))
        self.assertNotAlmostEqual(fixed[1][0],norm18[1][0])
        engine=Partitioned([[1.],[1.]])
        out=[engine.tick(1 if i==0 else 0,0,wet=.4,dry=.3,level=2) for i in range(2*B)]
        self.assertAlmostEqual(out[B][0],1.1,places=12)
        self.assertEqual(prepare([[0,0]],44100,48000,3),[[0,0,0],[0,0,0]])

    def test_resampling_duration_delay_and_gain(self):
        for src,dst in ((44100,48000),(48000,44100),(48000,96000),(44100,176400)):
            h=[0.]*256; h[64]=.5
            out=prepare([h],src,dst)[0]
            self.assertEqual(len(out),math.ceil(256*dst/src))
            self.assertAlmostEqual(sum(out),.5,delta=.002)
            peak=max(range(len(out)),key=lambda i:abs(out[i]))
            self.assertLessEqual(abs(peak-64*dst/src),1)
        h=[[.4,.2]]; self.assertEqual(prepare(h,48000,48000)[0],h[0])

    def test_capacity_crop_and_invalid(self):
        self.assertEqual(prepare([[.5]*1000],48000,48000,length_ms=10)[0],[.5]*480)
        with self.assertRaises(ValueError):prepare([[0.]*(MAX_FRAMES+1)],48000,48000)
        self.assertEqual(len(prepare([[0.]*(MAX_FRAMES+1)],48000,48000,length_ms=10)[0]),480)
        for channels,sr in (([[]],48000),([[math.nan]],48000),([[math.inf]],48000),([[1],[1],[1]],48000),([[1]],96000)):
            with self.assertRaises(ValueError):prepare(channels,sr,48000)

    def test_wav_missing_corrupt_formats(self):
        with tempfile.TemporaryDirectory() as d:
            path=Path(d)/'fixture.wav'
            with self.assertRaises(FileNotFoundError):read_wav(path)
            path.write_bytes(b'not a wav')
            with self.assertRaises((EOFError,wave.Error)):read_wav(path)
            for ch in (1,2):
                for sr in (44100,48000):
                    with wave.open(str(path),'wb') as w:
                        w.setnchannels(ch); w.setsampwidth(2); w.setframerate(sr)
                        w.writeframes((b'\x00\x20'+(b'\x00\xf0' if ch==2 else b''))*8)
                    data,rate=read_wav(path); self.assertEqual(rate,sr); self.assertEqual(len(data),ch); self.assertEqual(data[0][0],.25)
            # Reject actual unsupported and short WAV fixtures, not just metadata.
            for ch,sr in ((3,48000),(1,96000)):
                with wave.open(str(path),'wb') as w:
                    w.setnchannels(ch); w.setsampwidth(2); w.setframerate(sr); w.writeframes(bytes(16*ch*2))
                with self.assertRaises(ValueError):read_wav(path)
            with wave.open(str(path),'wb') as w:
                w.setnchannels(1); w.setsampwidth(2); w.setframerate(48000); w.writeframes(bytes(32))
            path.write_bytes(path.read_bytes()[:-4])
            with self.assertRaises(ValueError):read_wav(path)

    def test_silence_bypass_and_finite_levels(self):
        engine=Partitioned([[.5,.1],[.5,.1]])
        self.assertTrue(all(engine.tick(0,0)==(0.,0.) for _ in range(256)))
        rng=random.Random(42); samples=[]
        for i in range(512):
            x=rng.uniform(-.8,.8); samples.append(x)
            y=engine.tick(x,-x,enable=False)
            self.assertEqual(y,(samples[i-B],-samples[i-B]) if i>=B else (0.,0.))
        for i in range(256):self.assertTrue(all(map(math.isfinite,engine.tick(0,0))))

    def test_amp_bypass_pipeline_and_filters(self):
        a,b=Plexi(),Plexi(); engine=Partitioned([[1.],[1.]])
        expected=[]
        for i in range(512):
            x=.05*math.sin(i*.1); expected.append(a.tick(x,-x))
            self.assertEqual(engine.tick(*b.tick(x,-x),enable=False),expected[i-B] if i>=B else (0.,0.))
        for sr in (44100,48000):
            def rms(f,hp,lp):
                post=PostMix(sr,hp=hp,lp=lp); vals=[]
                for i in range(4000):
                    x=.1*math.sin(2*math.pi*f*i/sr); y=post.tick((x,0),(0,0))
                    self.assertEqual(y[1],0)
                    if i>=2000:vals.append(y[0])
                return math.sqrt(sum(v*v for v in vals)/len(vals))
            self.assertLess(rms(100,1000,0),rms(100,0,0)*.15)
            self.assertLess(rms(10000,0,1000),rms(10000,0,0)*.15)
        post=PostMix(wet_db=-120,dry_db=0,level_db=12,hp=1000,lp=2000)
        self.assertEqual(post.tick((1.,-1.),(.2,-.3)),(.2,-.3))
        post=PostMix(); post.set(wet_db=-6,dry_db=-120,level_db=6,hp=1000,lp=10000)
        prev=0
        for i in range(2000):
            x=.01*math.sin(i*.1); y=post.tick((x,0),(0,0))[0]
            self.assertTrue(math.isfinite(y)); self.assertLess(abs(y-prev),.02); prev=y
