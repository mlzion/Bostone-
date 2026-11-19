"""Actual-source v0.5 host regression and batch 64-frame timing proxy.
No Windows device callback or listening-test claim. Uses standard library only.
"""
import argparse
from array import array
import json
import math
from pathlib import Path
import tempfile
import run_reaper_cabinet as host

ROOT=Path(__file__).parents[1]


def probe(source,dynamic=False,mode_only=False,inject_invalid=False):
    host.GUARDS=(89,1023,2113,4095,4616,4699,4796,4896,65535,98304,131071,139264)
    s=host.instrument(source)
    # Replace FFT diagnostic channel with elapsed wall time per 64 processed samples.
    s=s.replace('probe_loads=0;', 'probe_frames=0; probe_peak=0; probe_fault=0; probe_loads=0;',1)
    begin='\nprobe_frames%64===0 ? probe_start=time_precise();\n'
    if dynamic:
        begin+='''probe_frames>3*srate ? (
  os_requested=floor(probe_frames/(0.13*srate))%3;
  pre_t=db((floor(probe_frames/(0.017*srate))%2)*36);
  power_t=db((floor(probe_frames/(0.023*srate))%2)*24);
  bass_t=(floor(probe_frames/(0.029*srate))%2);
  mid_t=(floor(probe_frames/(0.031*srate))%2);
  treble_t=(floor(probe_frames/(0.037*srate))%2);
  enable_t=!(probe_frames>5*srate && probe_frames<6*srate);
  cab_enable=!(probe_frames>7*srate && probe_frames<8*srate);
);
'''
    if mode_only:
        begin='\nprobe_frames%64===0 ? probe_start=time_precise();\nprobe_frames>3*srate ? os_requested=floor(probe_frames/(0.13*srate))%3;\n'
    if inject_invalid:
        begin+='probe_frames===srate ? (spl0=exp(1000); spl1=exp(1000)-exp(1000););\n'
    s=s.replace('@sample\n','@sample\n'+begin,1)
    s=s.replace('spl2=probe_loads', '!finite(spl0) || !finite(spl1) ? probe_fault=1; spl2=probe_loads')
    s=s.replace('spl3=(', 'spl3=(!probe_fault) && (')
    s=s.replace('spl4=probe_ffts*.000001;', 'probe_frames+=1; probe_frames%64===0 ? probe_peak=max(probe_peak,time_precise()-probe_start); spl4=probe_peak*10;')
    return s


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--reaper',required=True,type=Path)
    p.add_argument('--rates',default='44100,48000,96000');p.add_argument('--dynamic-only',action='store_true');p.add_argument('--inject-invalid',action='store_true');p.add_argument('--seconds',type=int,default=30);p.add_argument('--report',type=Path,required=True);a=p.parse_args();report=[]
    with tempfile.TemporaryDirectory(prefix='bostone-os-host-') as tmp:
        r=Path(tmp);(r/'Effects/Bostone').mkdir(parents=True);(r/'Data/BostoneIR').mkdir(parents=True);(r/'reaper.ini').write_text('[REAPER]\n')
        old=(ROOT/'jsfx/Bostone_Plexi_v0.4.jsfx').read_text();new=(ROOT/'jsfx/Bostone_Plexi_v0.5.jsfx').read_text()
        (r/'Effects/Bostone/Old.jsfx').write_text(old)
        (r/'Effects/Bostone/New.jsfx').write_text(probe(new,inject_invalid=a.inject_invalid))
        (r/'Effects/Bostone/Dynamic.jsfx').write_text(probe(new,True,inject_invalid=a.inject_invalid))
        (r/'Effects/Bostone/OldDynamic.jsfx').write_text(probe(old,True,inject_invalid=a.inject_invalid))
        (r/'Effects/Bostone/ModeOnly.jsfx').write_text(probe(new,mode_only=True,inject_invalid=a.inject_invalid))
        for rate in map(int,a.rates.split(',')):
            n=rate*a.seconds;quiet=rate//4
            x=[array('d',(0 if i<quiet else .06+.025*math.sin(i*.11) for i in range(n))),array('d',(0 if i<quiet else -.04+.015*math.sin(i*.07) for i in range(n)))]
            host.write_pcm(r/'input.wav',x,rate)
            ir_rate=min(rate,48000);length=4096 if rate<96000 else 2048
            ir=[[0.]*length,[0.]*length];ir[0][0]=.5;ir[0][-1]=.1;ir[1][0]=.3;ir[1][-1]=.07
            host.write_pcm(r/'Data/BostoneIR/fixture.wav',ir,ir_rate)
            def params(amp,cab,mode=None):
                s=f'{amp} 0 6 5 5 5 4 3 5 -12 {cab} 0 0 0 -120 0 0 0 fixture.wav'
                return s if mode is None else s+' '+str(mode)
            saved='BostoneIR/fixture.wav'
            reference_amp,_,_=host.render(a.reaper,r,f'base-amp-{rate}','Old.jsfx',params(1,0),rate,2,saved)
            reference_cab,_,_=host.render(a.reaper,r,f'base-cab-{rate}','Old.jsfx',params(0,1),rate,2,saved)
            for mode in (() if a.dynamic_only else (0,1,2)):
                for case,amp,cab in [('amp',1,0),('cabinet',0,1),('combined',1,1)]:
                    y,elapsed,version=host.render(a.reaper,r,f'{case}-{mode}-{rate}','New.jsfx',params(amp,cab,mode),rate,6,saved)
                    expected=reference_cab if case=='cabinet' else reference_amp if case=='amp' and mode==0 else None
                    error=max(abs(u-v) for c in range(2) for u,v in zip(y[c],expected[c])) if expected else None
                    if error is not None:assert error<.000002,(case,mode,rate,error)
                    for ch in range(2):
                        assert max(abs(v) for v in y[ch][:quiet-256])<.000002,'silence'
                        assert all(math.isfinite(v) for v in y[ch])
                        assert max(map(abs,y[ch]))<.4,'unexpected default peak'
                        for start in range(quiet+8192,n-1024,1024):
                            assert max(abs(v) for v in y[ch][start:start+1024])>.00001,'dropout'
                    assert max(abs(v-.01) for v in y[2][256:-256])<.000002,'reloaded IR'
                    assert max(abs(v-.125) for v in y[3][256:-256])<.000002,'memory corruption'
                    assert max(abs(v-.25) for v in y[5][256:-256])<.000002,'IR failed'
                    entry=dict(rate=rate,mode=mode,case=case,audio_seconds=a.seconds,render_seconds=elapsed,version=version,error=error,
                               peak=max(max(map(abs,c)) for c in y[:2]),peak_64_sample_wall_seconds=max(y[4])/10,passed=True)
                    report.append(entry);print(json.dumps(entry),flush=True)
            y,elapsed,version=host.render(a.reaper,r,f'dynamic-{rate}','Dynamic.jsfx',params(1,1,0),rate,6,saved)
            assert max(abs(v-.01) for v in y[2][256:-256])<.000002,'mode change reloaded IR'
            assert max(abs(v-.125) for v in y[3][256:-256])<.000002,'automation corrupted memory'
            assert max(abs(v-.25) for v in y[5][256:-256])<.000002,'automation lost cabinet'
            # Very high pre/power drive makes steep waveform edges even in v0.4.
            # Compare identical target automation to v0.4 rather than labeling
            # every steep saturated edge a control click.
            old_dynamic,_,_=host.render(a.reaper,r,f'old-dynamic-{rate}','OldDynamic.jsfx',params(1,1),rate,6,saved)
            baseline_step=max(abs(v-u) for c in old_dynamic[:2] for u,v in zip(c,c[1:]))
            step=max(abs(v-u) for c in y[:2] for u,v in zip(c,c[1:]))
            assert step<max(.02,baseline_step*1.1),('excess transition over v0.4',step,baseline_step)
            assert max(max(map(abs,c)) for c in y[:2])<.5
            report.append(dict(rate=rate,case='rapid-mode-and-gain-automation',injected_invalid=a.inject_invalid,version=version,audio_seconds=a.seconds,render_seconds=elapsed,max_step=step,v04_reference_max_step=baseline_step,peak_64_sample_wall_seconds=max(y[4])/10,passed=True));print(json.dumps(report[-1]),flush=True)
            # Isolate mode-switch transients with a low-level 100 Hz sine,
            # not the steep high-drive waveform used by the stress test.
            mode_input=[array('d',(0 if i<quiet else .001*math.sin(2*math.pi*100*i/rate) for i in range(n))),array('d',[0.])*n]
            host.write_pcm(r/'input.wav',mode_input,rate)
            mode_y,elapsed,version=host.render(a.reaper,r,f'mode-only-{rate}','ModeOnly.jsfx',params(1,1,0),rate,6,saved)
            step=max(abs(v-u) for c in mode_y[:2] for u,v in zip(c,c[1:]));assert step<.0005,('low-level mode-only discontinuity',step)
            assert max(abs(v-.01) for v in mode_y[2][256:-256])<.000002
            assert max(abs(v-.125) for v in mode_y[3][256:-256])<.000002
            assert max(map(abs,mode_y[1]))<.000002,'mode switch stereo crossfeed'
            for start in range(quiet+8192,n-1024,1024):
                assert max(abs(v) for v in mode_y[0][start:start+1024])>.00001,'mode switch dropout'
            report.append(dict(rate=rate,case='mode-only-transitions',injected_invalid=a.inject_invalid,version=version,audio_seconds=a.seconds,render_seconds=elapsed,max_step=step,passed=True));print(json.dumps(report[-1]),flush=True)
    a.report.write_text(json.dumps(report,indent=2)+'\n');print(f'{len(report)} host cases passed')


if __name__=='__main__':main()
