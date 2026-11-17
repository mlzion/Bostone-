"""Original numerical reference, NOT an EEL2 interpreter or REAPER runtime."""
import math

DEFAULT=dict(enable=1,input_db=0,pre_db=6,bass=5,mid=5,treble=5,presence=4,power_db=3,tight=5,output_db=-12)
LIMITS=dict(enable=(0,1),input_db=(-24,24),pre_db=(0,36),bass=(0,10),mid=(0,10),treble=(0,10),presence=(0,10),power_db=(0,24),tight=(0,10),output_db=(-36,0))


def inverse(a):
    n=len(a)
    a=[row[:]+[float(i==j) for j in range(n)] for i,row in enumerate(a)]
    for k in range(n):
        p=a[k][k]
        assert p>0 and math.isfinite(p)
        a[k]=[x/p for x in a[k]]
        for i in range(n):
            if i!=k:
                f=a[i][k]
                a[i]=[x-f*y for x,y in zip(a[i],a[k])]
    return [row[n:] for row in a]


def tone_matrix(sr,b,m,t,complex_frequency=None):
    # Independent nodal stamping. For AC reference use j*w*C instead of companion G.
    cs=[500e-12,22e-9,22e-9]
    gs=[2*sr*c if complex_frequency is None else 2j*math.pi*complex_frequency*c for c in cs]
    a=[[0.]*5 for _ in range(5)]
    def stamp(i,j,g):
        a[i][i]+=g
        if j>=0:
            a[j][j]+=g; a[i][j]-=g; a[j][i]-=g
    rb=max(100,1e6*b*b)+max(25,25000*(1-m))
    rm=max(25,25000*m)
    stamp(0,-1,1/33000); stamp(1,-1,gs[0]); stamp(0,2,gs[1]); stamp(0,3,gs[2])
    stamp(2,3,1/rb); stamp(3,-1,1/rm)
    stamp(1,4,1/max(100,220000*(1-t))); stamp(4,2,1/max(100,220000*t)); stamp(4,-1,1/2e6)
    return a,gs


def solve_complex(a,b):
    # Pivoting AC solver independently verifies the time-domain companion network.
    a=[list(map(complex,row))+[complex(v)] for row,v in zip(a,b)]
    for k in range(len(a)):
        p=max(range(k,len(a)),key=lambda i:abs(a[i][k])); a[k],a[p]=a[p],a[k]
        d=a[k][k]; a[k]=[x/d for x in a[k]]
        for i in range(len(a)):
            if i!=k:
                d=a[i][k]; a[i]=[x-d*y for x,y in zip(a[i],a[k])]
    return [row[-1] for row in a]


class Tone:
    def __init__(self,sr,b=.5,m=.5,t=.5):
        self.sr=sr; self.set(b,m,t)
        self.h=[[0.]*3 for _ in range(2)]

    def set(self,b,m,t):
        a,self.gs=tone_matrix(self.sr,b,m,t); self.inv=inverse(a)

    def tick(self,x,ch):
        ht,hb,hm=self.h[ch]; ct,cb,cm=self.gs
        rhs=[x/33000-hb-hm,ct*x-ht,hb,hm,0]
        s,t,b,w,o=[sum(v*r for v,r in zip(row,rhs)) for row in self.inv]
        self.h[ch]=[-2*ct*(t-x)-ht,-2*cb*(s-b)-hb,-2*cm*(s-w)-hm]
        self.h[ch]=[0. if abs(v)<1e-30 else v for v in self.h[ch]]
        return o


def current(x):
    q=max(0,x)+math.log1p(math.exp(-abs(x)))
    return q/(1+q)


def triode(x,bias):
    return math.tanh(x+bias)-math.tanh(bias)


class Plexi:
    def __init__(self,sr=48000,**changes):
        self.sr=sr; self.p=DEFAULT|changes
        self.alpha=1-math.exp(-1/(.020*sr)); self.ramp=1/(.010*sr)
        self.g=self.targets(); self.tone=Tone(sr,self.g['bass'],self.g['mid'],self.g['treble'])
        self.last=[self.g[k] for k in ('bass','mid','treble')]; self.counter=0
        self.c={k:self.pole(f) for k,f in dict(input_hp=35,input_lp=18000,bright=190,dc=10,presence=1200,output=10000).items()}
        self.attack=1-math.exp(-1/(.010*sr)); self.release=1-math.exp(-1/(.150*sr))
        self.state=[[0.]*10 for _ in range(2)]

    def pole(self,f): return 1-math.exp(-2*math.pi*min(f,.45*self.sr)/self.sr)

    def targets(self):
        p=self.p
        return dict(enable=float(p['enable']>=.5),input=10**(p['input_db']/20),pre=10**(p['pre_db']/20),
                    bass=p['bass']/10,mid=p['mid']/10,treble=p['treble']/10,presence=1.2*p['presence']/10,
                    power=10**(p['power_db']/20),tight=self.pole(70*math.exp(math.log(300/70)*p['tight']/10)),
                    output=10**(p['output_db']/20))

    def set(self,**changes):
        for k,v in changes.items():
            lo,hi=LIMITS[k]; self.p[k]=max(lo,min(hi,v)) if math.isfinite(v) else lo

    def amp(self,x,ch):
        s=self.state[ch]; c=self.c; g=self.g
        def lp(index,x,k):
            s[index]+=k*(x-s[index]); return s[index]
        v=max(-16,min(16,x))*g['input']; v-=lp(0,v,c['input_hp']); v=lp(1,v,c['input_lp'])
        v+=.9*(v-lp(2,v,c['bright'])); v=triode(.8*g['pre']*v,.22)
        v-=lp(3,v,g['tight']); u=3*v+.1; v=u/(1+abs(u))-.1/1.1
        v-=lp(4,v,c['dc']); v=3*self.tone.tick(v,ch)
        pa=triode(2*v,.04); pb=triode(-1.9*v,.04)
        target=.5*(abs(pa)+abs(pb)); rate=self.attack if target>s[9] else self.release
        s[9]+=rate*(target-s[9]); rail=1/(1+.18*s[9])
        v=2*rail*(current(3*(g['power']*pa-.1))-current(3*(g['power']*pb-.1)))
        v-=lp(5,v,c['dc']); v+=g['presence']*(v-lp(6,v,c['presence']))
        v=lp(8,lp(7,v,c['output']),c['output'])
        y=.8*math.tanh(v/.8)*g['output']
        self.state[ch]=[0. if abs(v)<1e-30 else v for v in s]
        return y

    def tick(self,l,r):
        for k,v in self.targets().items():
            d=v-self.g[k]
            self.g[k]+=max(-self.ramp,min(self.ramp,d)) if k=='enable' else self.alpha*d
        self.counter+=1
        if self.counter>=16:
            self.counter=0; values=[self.g[k] for k in ('bass','mid','treble')]
            if sum(abs(a-b) for a,b in zip(values,self.last))>1e-7:
                self.tone.set(*values); self.last=values
        out=[]
        for ch,x in enumerate((l,r)):
            dry=x if math.isfinite(x) else 0.; wet=self.amp(dry,ch)
            out.append(dry if self.g['enable']==0 else (1-self.g['enable'])*dry+self.g['enable']*wet)
        return tuple(out)
