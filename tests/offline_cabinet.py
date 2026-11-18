"""Independent cabinet reference. Does not execute JSFX or REAPER's decoder/SRC.
Generated fixtures only; no external IR assets. Standard library only.
"""
import cmath
import math
import wave
from pathlib import Path

B=64
MAX_FRAMES=32768


def fft(x,inverse=False):
    """Original radix-2 test FFT. REAPER supplies its own FFT in production."""
    a=list(map(complex,x)); n=len(a); j=0
    for i in range(1,n):
        bit=n>>1
        while j&bit:j^=bit; bit>>=1
        j^=bit
        if i<j:a[i],a[j]=a[j],a[i]
    length=2
    while length<=n:
        root=cmath.exp((2j if inverse else -2j)*math.pi/length)
        for start in range(0,n,length):
            w=1
            for k in range(length//2):
                u=a[start+k]; v=a[start+k+length//2]*w
                a[start+k]=u+v; a[start+k+length//2]=u-v; w*=root
        length*=2
    return [v/n for v in a] if inverse else a


def resample_reference(channels,src,dst):
    # Windowed-sinc offline oracle; not a replica of REAPER file_riff's SRC.
    if src==dst:return [c[:] for c in channels]
    count=math.ceil(len(channels[0])*dst/src)
    ratio=dst/src; cutoff=min(1,ratio); radius=24
    result=[]
    for data in channels:
        out=[]
        for i in range(count):
            p=i/ratio; total=0.
            for j in range(max(0,math.ceil(p-radius)),min(len(data),math.floor(p+radius)+1)):
                d=p-j; u=cutoff*d
                sinc=1. if u==0 else math.sin(math.pi*u)/(math.pi*u)
                win=.5*(1+math.cos(math.pi*d/radius))
                total+=data[j]*cutoff*sinc*win
            out.append(total)
        result.append(out)
    return result


def prepare(channels,src,dst,mode=0,length_ms=0):
    if src not in (44100,48000) or len(channels) not in (1,2):raise ValueError('format')
    if not channels[0] or any(len(c)!=len(channels[0]) for c in channels):raise ValueError('length')
    if not all(math.isfinite(v) for c in channels for v in c):raise ValueError('nonfinite')
    count=math.ceil(len(channels[0])*dst/src)
    if length_ms>0:count=min(count,max(1,math.floor(dst*length_ms/1000)))
    if count>MAX_FRAMES:raise ValueError('capacity')
    out=[c[:count] for c in resample_reference(channels,src,dst)]
    peak=max(abs(v) for c in out for v in c)
    scale=src/dst
    if mode==1:scale*=10**(-18/20)
    if mode in (2,3) and peak>0:scale=(1 if mode==2 else 10**(-18/20))/peak
    out=[[v*scale for v in c] for c in out]
    return out if len(out)==2 else [out[0],out[0][:]]


def read_wav(path):
    # PCM oracle for fixture tests; production uses REAPER's native media decoder.
    if Path(path).suffix.lower()!='.wav':raise ValueError('extension')
    with wave.open(str(path),'rb') as f:
        ch=f.getnchannels(); sr=f.getframerate(); width=f.getsampwidth(); n=f.getnframes()
        if ch not in (1,2) or sr not in (44100,48000) or width not in (1,2,3,4) or not n:raise ValueError('format')
        raw=f.readframes(n)
        if len(raw)!=n*ch*width:raise ValueError('short')
        values=[]
        for i in range(0,len(raw),width):
            v=(raw[i]-128)/128 if width==1 else int.from_bytes(raw[i:i+width],'little',signed=True)/(2**(8*width-1))
            values.append(v)
        return [values[c::ch] for c in range(ch)],sr


class Partitioned:
    def __init__(self,channels,block=B):
        self.b=block
        self.parts=math.ceil(len(channels[0])/self.b)
        self.h=[[fft(c[p*self.b:(p+1)*self.b]+[0.]*(2*self.b-len(c[p*self.b:(p+1)*self.b]))) for p in range(self.parts)] for c in channels]
        self.hist=[[[0j]*(2*self.b) for _ in range(self.parts)] for _ in range(2)]
        self.input=[[0.]*self.b for _ in range(2)]; self.output=[[0.]*self.b for _ in range(2)]; self.overlap=[[0.]*self.b for _ in range(2)]
        self.head=0; self.pos=0; self.delay=[[0.]*self.b for _ in range(2)]

    def tick(self,l,r,enable=True,wet=1,dry=0,level=1):
        idx=self.pos; result=[]
        for ch,x in enumerate((l,r)):
            aligned=self.delay[ch][idx]; self.delay[ch][idx]=x
            y=self.output[ch][idx]
            result.append((dry*aligned+wet*level*y) if enable else aligned)
            self.input[ch][idx]=x
        self.pos+=1
        if self.pos==self.b:
            self.pos=0
            for ch in range(2):
                self.hist[ch][self.head]=fft(self.input[ch]+[0.]*self.b)
                total=[0j]*(2*self.b)
                for p in range(self.parts):
                    x=self.hist[ch][(self.head-p)%self.parts]; h=self.h[ch][p]
                    total=[a+b*c for a,b,c in zip(total,x,h)]
                out=fft(total,True)
                self.output[ch]=[out[i].real+self.overlap[ch][i] for i in range(self.b)]
                self.overlap[ch]=[out[i+self.b].real for i in range(self.b)]
            self.head=(self.head+1)%self.parts
        return tuple(result)


def direct(x,h):
    y=[0.]*(len(x)+len(h)-1)
    for i,a in enumerate(x):
        for j,b in enumerate(h):y[i+j]+=a*b
    return y


class PostMix:
    """Steady routing plus smoothed cabinet controls, separate stereo filter state."""
    def __init__(self,sr=48000,wet_db=0,dry_db=-120,level_db=0,hp=0,lp=0):
        self.sr=sr; self.alpha=1-math.exp(-1/(.020*sr)); self.step=1/(.010*sr)
        self.state=[[0.,0.],[0.,0.]]
        self.target={}; self.g={}
        self.set(wet_db,dry_db,level_db,hp,lp); self.g=self.target.copy()

    def set(self,wet_db=0,dry_db=-120,level_db=0,hp=0,lp=0):
        gain=lambda v:0. if v<=-120 else 10**(v/20)
        pole=lambda f:1-math.exp(-2*math.pi*min(max(1,f),.45*self.sr)/self.sr)
        self.target=dict(wet=gain(wet_db),dry=gain(dry_db),level=10**(level_db/20),hp=pole(hp),lp=pole(lp),hpm=float(hp>0),lpm=float(lp>0))

    def tick(self,wet,dry):
        for k,t in self.target.items():
            d=t-self.g[k]; self.g[k]+=max(-self.step,min(self.step,d)) if k in ('hpm','lpm') else self.alpha*d
        out=[]
        for ch,(w,d) in enumerate(zip(wet,dry)):
            s=self.state[ch]; g=self.g
            s[0]+=g['hp']*(w-s[0]); w-=g['hpm']*s[0]
            s[1]+=g['lp']*(w-s[1]); w+=g['lpm']*(s[1]-w)
            out.append(g['dry']*d+g['wet']*g['level']*w)
        return tuple(out)


class Hybrid:
    """64-frame first 256 taps; 256-frame remainder plus 64-frame alignment."""
    def __init__(self,channels):
        self.head=Partitioned([c[:256] for c in channels])
        self.tail=Partitioned([c[256:] for c in channels],256) if len(channels[0])>256 else None
        self.delay=[[0.]*64 for _ in range(2)]; self.pos=0

    def tick(self,l,r):
        head=self.head.tick(l,r)
        if self.tail is None:return head
        tail=self.tail.tick(l,r); out=[]
        for ch in range(2):
            out.append(head[ch]+self.delay[ch][self.pos]); self.delay[ch][self.pos]=tail[ch]
        self.pos=(self.pos+1)%64
        return tuple(out)
