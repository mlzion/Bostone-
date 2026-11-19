"""Optional actual-REAPER spectra benchmark (requires NumPy for analysis only).
Synthetic stepped coherent-sine sweeps; no external recordings or IRs.
"""
import argparse
import json
import math
from pathlib import Path
import tempfile
import wave
try:
    import resource
except ImportError:
    resource=None
import numpy as np
from run_reaper_cabinet import render, write_pcm, read_pcm, ROOT


def stimulus(rate):
    n=8192
    segments=[]; values=[0.]*int(.3*rate)
    for level in (.00001,.01,.1,.5):
        for hz in (200,1000,3000,6000,10000):
            k=round(hz*n/rate); k+=int(k%2==0); f=k*rate/n
            settle=int(.7*rate); start=len(values)
            values.extend(level*np.sin(2*np.pi*f*np.arange(settle+n)/rate))
            segments.append(dict(level=level,hz=f,bin=k,start=start+settle,n=n))
    return values,segments


def spectrum(values,segment):
    a=np.asarray(values[segment['start']:segment['start']+segment['n']]);n=len(a)
    power=np.abs(np.fft.rfft(a))**2
    fundamental=segment['bin']; valid=np.zeros(len(power),dtype=bool);valid[0:2]=True
    for k in range(fundamental,len(power),fundamental):valid[max(0,k-1):k+2]=True
    den=max(power[fundamental],1e-30)
    return dict(peak=float(np.max(np.abs(a))),fundamental_amplitude=float(2*np.sqrt(den)/n),
                nonharmonic_db=float(10*np.log10(max(float(power[~valid].sum()),1e-30)/den)),
                harmonics_db=[float(10*np.log10(max(power[h*fundamental],1e-30)/den)) for h in range(2,9) if h*fundamental<len(power)])


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--reaper',type=Path,required=True)
    p.add_argument('--source',type=Path,default=ROOT/'jsfx/Bostone_Plexi_v0.4.jsfx');p.add_argument('--report',type=Path,required=True)
    p.add_argument('--modes',default='0');args=p.parse_args();report=[]
    with tempfile.TemporaryDirectory(prefix='bostone-spectrum-') as tmp:
        r=Path(tmp);(r/'Effects/Bostone').mkdir(parents=True);(r/'reaper.ini').write_text('[REAPER]\n')
        source=args.source.read_text();(r/'Effects/Bostone/Measure.jsfx').write_text(source)
        for rate in (44100,48000,96000):
            x,segments=stimulus(rate)
            pcm=np.zeros((len(x),2),dtype='<i4');pcm[:,0]=np.rint(np.asarray(x)*2147483647).astype('<i4')
            with wave.open(str(r/'input.wav'),'wb') as wav:
                wav.setnchannels(2);wav.setsampwidth(4);wav.setframerate(rate);wav.writeframes(pcm.tobytes())
            for mode in map(int,args.modes.split(',')):
                params='1 0 6 5 5 5 4 3 5 -12 0 0 0 0 -120 0 0 0 None'
                if 'slider20:' in source:params+=' '+str(mode)
                cpu0=resource.getrusage(resource.RUSAGE_CHILDREN) if resource else None
                y,elapsed,version=render(args.reaper.resolve(),r,f'm{mode}-{rate}','Measure.jsfx',params,rate,2)
                cpu1=resource.getrusage(resource.RUSAGE_CHILDREN) if resource else None
                cpu_seconds=(cpu1.ru_utime+cpu1.ru_stime-cpu0.ru_utime-cpu0.ru_stime) if cpu1 else None
                assert np.isfinite(y).all()
                assert max(map(abs,y[1]))<.000001,'stereo crossfeed'
                entry=dict(source=args.source.name,rate=rate,mode=mode,version=version,audio_seconds=len(x)/rate,render_seconds=elapsed,child_process_cpu_seconds=cpu_seconds,
                           peak=max(map(abs,y[0])),measurements=[dict(**s,**spectrum(y[0],s)) for s in segments])
                report.append(entry);print(json.dumps({k:v for k,v in entry.items() if k!='measurements'}),flush=True)
    args.report.write_text(json.dumps(report,indent=2)+'\n')


if __name__=='__main__':main()
