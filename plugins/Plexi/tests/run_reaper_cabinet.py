"""Optional actual-host integration regression. Requires a user-provided REAPER.
Usage: python3 plugins/Plexi/tests/run_reaper_cabinet.py --reaper /path/to/reaper --report /tmp/report.json
No REAPER binary, external IR, or WDL implementation is bundled/downloaded here.
An isolated resource directory and synthetic PCM WAVs are generated temporarily.
"""
import argparse
from array import array
import base64
import struct
import json
import math
from pathlib import Path
import re
import subprocess
import tempfile
import time
import wave

ROOT=Path(__file__).parents[1]
GUARDS=(89,1023,2048,65535,98304,131071,139264)


def write_pcm(path,channels,rate):
    with wave.open(str(path),'wb') as w:
        w.setnchannels(len(channels));w.setsampwidth(2);w.setframerate(rate)
        raw=bytearray()
        for i in range(len(channels[0])):
            for c in channels:raw.extend(int(max(-32768,min(32767,round(c[i]*32768)))).to_bytes(2,'little',signed=True))
        w.writeframes(raw)


def read_pcm(path):
    with wave.open(str(path),'rb') as w:
        nch=w.getnchannels();width=w.getsampwidth();rate=w.getframerate();raw=w.readframes(w.getnframes())
    values=[array('d') for _ in range(nch)]
    for i in range(0,len(raw),width):values[(i//width)%nch].append(int.from_bytes(raw[i:i+width],'little',signed=True)/2**(8*width-1))
    return values,rate


def instrument(source):
    # Test-only diagnostic channels: load count, memory guards, FFT count, ready.
    # Original two-channel processing and controls are not changed.
    source=source.replace('out_pin:Right','out_pin:Right\nout_pin:Loads\nout_pin:Guards\nout_pin:FFT calls\nout_pin:Ready',1)
    source=source.replace('function cab_load() local(', 'function cab_load() local(',1)
    at=source.index('  cab_ready=0;',source.index('function cab_load()'))
    source=source[:at]+'  probe_loads+=1;\n'+source[at:]
    at=source.index('  memset(work,0,128)',source.index('function cab_block_channel('))
    source=source[:at]+'  probe_ffts+=1;\n'+source[at:]
    setup='\nprobe_loads=0; probe_ffts=0;\n'+''.join(f'{i}[0]=7.25;\n' for i in GUARDS)
    source=source.replace('\n@slider',setup+'\n@slider',1)
    check=' && '.join(f'({i}[0]===7.25)' for i in GUARDS)
    probe=f'\nspl2=probe_loads*.01; spl3=({check}) ? .125 : -.125; spl4=probe_ffts*.000001; spl5=cab_ready ? .25 : -.25;\n'
    return source.replace('\n@serialize',probe+'\n@serialize',1)


def render(exe,resource,name,fx,params,rate,nch=6,saved_path=None):
    output=resource/(name+'.wav');job=resource/(name+'.txt')
    chain=f'<FXCHAIN\nSHOW 0\nLASTSEL 0\nDOCKED 0\nBYPASS 0 0 0\n<JS Bostone/{fx} ""\n'+params+'\n>\nWAK 0 0\n>\n'
    if saved_path is not None:
        payload=struct.pack('<fI',1,len(saved_path.encode()))+saved_path.encode()+bytes(2)
        chain=chain.replace('>\nWAK','>\n<JS_SER\n'+base64.b64encode(payload).decode()+'\n>\nWAK')
    job.write_text(str(resource/'input.wav')+'\t'+str(output)+'\n<CONFIG\nSRATE '+str(rate)+'\nNCH '+str(nch)+'\nFX_NCH '+str(nch)+'\n'+chain+'>\n')
    start=time.perf_counter()
    result=subprocess.run([str(exe),'-newinst','-nosplash','-ignoreerrors','-cfgfile',str(resource/'reaper.ini'),'-batchconvert',str(job)],capture_output=True,text=True,timeout=180)
    elapsed=time.perf_counter()-start
    log=Path(str(job)+'.log').read_text() if Path(str(job)+'.log').exists() else ''
    if result.returncode or 'ERROR:' in log or not output.exists():raise AssertionError((name,log,result.stdout,result.stderr))
    data,actual=read_pcm(output)
    assert actual==rate and len(data)==nch,(name,actual,len(data))
    version=re.search(r'REAPER ([^:]+):',result.stdout+result.stderr)
    return data,elapsed,version[1] if version else 'unknown'


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--reaper',required=True,type=Path);parser.add_argument('--report',type=Path)
    parser.add_argument('--seconds',type=int,default=30,help='Use >=25 to cover repeated reported 10-second cycles')
    args=parser.parse_args();exe=args.reaper.resolve(); report=[]
    with tempfile.TemporaryDirectory(prefix='bostone-native-') as tmp:
        r=Path(tmp);(r/'Effects/Bostone').mkdir(parents=True);(r/'Data/BostoneIR').mkdir(parents=True)
        (r/'reaper.ini').write_text('[REAPER]\n')
        source=(ROOT/'jsfx/Bostone_Plexi_v0.4.jsfx').read_text()
        probe=instrument(source)
        (r/'Effects/Bostone/HostProbe.jsfx').write_text(probe)
        toggle=probe.replace('probe_loads=0;', 'probe_clock=0; probe_loads=0;',1)
        toggle=toggle.replace('@sample\n','@sample\nprobe_clock+=1; cab_enable=!(probe_clock>=11*srate && probe_clock<13*srate);\n',1)
        (r/'Effects/Bostone/HostToggle.jsfx').write_text(toggle)
        restored=probe.replace('probe_loads=0;', 'probe_clock=0; probe_loads=0;',1)
        restored=restored.replace('@sample\n','@sample\nprobe_clock+=1; (probe_clock===10*srate || probe_clock===20*srate) ? (strcpy(#cab_prior_restore,#cab_file); cab_restore_selection(););\n',1)
        (r/'Effects/Bostone/HostRestore.jsfx').write_text(restored)
        (r/'Effects/Bostone/Bostone_Plexi_v0.3.jsfx').write_text((ROOT/'jsfx/Bostone_Plexi_v0.3.jsfx').read_text())
        for rate in (44100,48000):
            length=rate*args.seconds; silence=rate//4
            x=[array('d',(0. if i<silence else .04+.02*math.sin(i*.11) for i in range(length))),
               array('d',(0. if i<silence else -.03+.01*math.sin(i*.07) for i in range(length)))]
            write_pcm(r/'input.wav',x,rate);x,_=read_pcm(r/'input.wav')
            taps=[(0,.5),(63,.01),(64,.02),(255,.03),(256,.04),(257,.05),(511,.06),(512,.07),(1024,.08),(4095,.04)]
            ir=[[0.]*4096,[0.]*4096]
            for k,v in taps:ir[0][k]=v;ir[1][k]=v*.6
            write_pcm(r/'Data/BostoneIR/fixture.wav',ir,rate);ir,_=read_pcm(r/'Data/BostoneIR/fixture.wav')
            old_params='1 0 6 5 5 5 4 3 5 -12'
            old,_,_=render(exe,r,f'old-{rate}','Bostone_Plexi_v0.3.jsfx',old_params,rate,2)
            for name,amp,cab,have_ir in [('dry',0,0,True),('amp',1,0,True),('wet',0,1,True),('missing',0,1,False),('toggle',0,1,True),('oversized',0,1,True),('cropped',0,1,True),('restored',0,1,True)]:
                if name=='toggle' and args.seconds<25:continue
                current_ir=[list(c)+([.02] if name in ('oversized','cropped') else []) for c in ir]
                write_pcm(r/'Data/BostoneIR/fixture.wav',current_ir,rate)
                current_ir,_=read_pcm(r/'Data/BostoneIR/fixture.wav')
                ready_expected=have_ir and name!='oversized'
                crop=80 if name=='cropped' else 0
                file='fixture.wav' if have_ir else 'ERR'
                params=f'{amp} 0 6 5 5 5 4 3 5 -12 {cab} 0 0 0 -120 0 0 {crop} {file}'
                y,seconds,version=render(exe,r,f'{name}-{rate}','HostToggle.jsfx' if name=='toggle' else ('HostRestore.jsfx' if name=='restored' else 'HostProbe.jsfx'),params,rate,saved_path='BostoneIR/fixture.wav' if have_ir else 'BostoneIR/missing.wav')
                # Native PDC aligns output: expected FIR delay is the IR's own delay only.
                max_error=0.
                for ch in range(2):
                    for i,v in enumerate(y[ch]):
                        if name=='toggle' and not (11.1*rate<i<12.9*rate or i>13.5*rate):continue
                        if name=='toggle' and i<12.9*rate:expected=x[ch][i]
                        elif name=='amp':expected=old[ch][i]
                        elif cab and ready_expected:expected=sum(current_ir[ch][k]*x[ch][i-k] for k,_ in taps+([(4096,.02)] if name=='cropped' else []) if i>=k and (not crop or k<math.floor(rate*crop/1000)))
                        else:expected=x[ch][i]
                        max_error=max(max_error,abs(v-expected))
                assert max_error<2e-6,(name,rate,'audio mismatch/gap',max_error)
                # Discard PDC padding at the end of diagnostic channels.
                for values,target in ((y[2],.01),(y[3],.125),(y[5],.25 if ready_expected else -.25)):
                    assert max(abs(v-target) for v in values[128:-128])<2e-6,(name,rate,'repeated load/buffer corruption/IR failure')
                if not cab:assert max(map(abs,y[4]))<2e-6,(name,rate,'FFT ran while bypassed')
                if cab and ready_expected:
                    assert max(y[4])>.001,(name,rate,'FFT never ran')
                    assert max(b-a for a,b in zip(y[4][128:-129],y[4][129:-128]))<.000003,(name,rate,'periodic FFT burst')
                # Continuous plateau/sine after warm-up: no periodic silent windows.
                if name in ('dry','wet','missing','toggle','oversized','cropped','restored'):
                    for start in range(silence+4096,length-1024,1024):
                        assert min(y[0][start:start+1024])>.009,(name,rate,'silent window')
                if name=='toggle':
                    counts=y[4][int(11.1*rate):int(12.9*rate)]
                    assert max(counts)==min(counts),'FFT work continued in bypass'
                report.append(dict(case=name,rate=rate,audio_seconds=args.seconds,version=version,render_seconds=seconds,max_error=max_error,passed=True))
                print(json.dumps(report[-1]),flush=True)
    if args.report:args.report.write_text(json.dumps(report,indent=2)+'\n')
    print(f'{len(report)} native REAPER cases passed')


if __name__=='__main__':main()
