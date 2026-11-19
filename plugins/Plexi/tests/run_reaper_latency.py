"""Native test-only identity amplifier isolates FIR delay/phase and PDC."""
import argparse
import json
from pathlib import Path
import tempfile
from run_reaper_cabinet import ROOT,render,write_pcm,read_pcm
from test_oversampling import coefficients,roundtrip


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--reaper',type=Path,required=True);p.add_argument('--report',type=Path,required=True);args=p.parse_args();report=[]
    source=(ROOT/'jsfx/Bostone_Plexi_v0.5.jsfx').read_text();h=coefficients(source)
    a=source.index('function amp(x)');b=source.index('// OVERSAMPLING:',a)
    source=source[:a]+'function amp(x) (x;);\n'+source[b:]
    with tempfile.TemporaryDirectory(prefix='bostone-latency-') as tmp:
        r=Path(tmp);(r/'Effects/Bostone').mkdir(parents=True);(r/'reaper.ini').write_text('[REAPER]\n');(r/'Effects/Bostone/Identity.jsfx').write_text(source)
        for rate in (44100,48000,96000):
            n=rate;at=rate//4;x=[0.]*n;x[at]=.1;write_pcm(r/'input.wav',[x,[0.]*n],rate);quantized,_=read_pcm(r/'input.wav');amplitude=quantized[0][at]
            for mode,delay in ((0,0),(1,32),(2,48)):
                y,elapsed,version=render(args.reaper,r,f'identity-{rate}-{mode}','Identity.jsfx',f'1 0 6 5 5 5 4 3 5 -12 0 0 0 0 -120 0 0 0 None {mode}',rate,2)
                kernel=roundtrip([amplitude],h,mode)
                expected=[0.]*len(y[0])
                for i,v in enumerate(kernel):
                    if 0<=at+i-delay<len(expected):expected[at+i-delay]=v
                error=max(abs(a-b) for a,b in zip(y[0],expected));assert error<.000002,(rate,mode,error)
                assert max(map(abs,y[1]))<.000002
                assert max(range(len(y[0])),key=lambda i:abs(y[0][i]))==at,(rate,mode,'PDC peak shift')
                report.append(dict(rate=rate,mode=mode,version=version,max_error=error,compensated_peak_frame=at,expected_peak_frame=at,passed=True))
    args.report.write_text(json.dumps(report,indent=2)+'\n');print(f'{len(report)} native identity/PDC cases passed')


if __name__=='__main__':main()
