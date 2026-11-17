"""Independent standard-library numerical model, NOT a JSFX/EEL2 runtime.
Run: python3 -m unittest discover -s tests -v
Production code is jsfx/Bostone_Preamp.jsfx; this model is only test support.
"""
import math

DEFAULT = dict(input_db=0, hp=80, pre_gain=0, pre_freq=400, lp=10000,
               pre=1, drive=3, dist=1, low=0, mid=0, mid_freq=1200, high=0,
               post=1, output_db=-6, master=0, input=1, output=1)
RANGES = dict(input_db=(-24,24), hp=(40,300), pre_gain=(-12,12),
              pre_freq=(150,1000), lp=(2000,15000), drive=(1,20),
              low=(-12,12), mid=(-12,12), mid_freq=(400,4000), high=(-12,12),
              output_db=(-24,12))


def coeff(kind, f, gain, sr):
    w = 2*math.pi*min(.45*sr, max(10,f))/sr
    c, s = math.cos(w), math.sin(w)
    a = s/(2*math.sqrt(.5))
    A = 10**(gain/40)
    if kind == 'hp':
        b = [(1+c)/2, -(1+c), (1+c)/2]
        d = [1+a, -2*c, 1-a]
    elif kind == 'lp':
        b = [(1-c)/2, 1-c, (1-c)/2]
        d = [1+a, -2*c, 1-a]
    elif kind == 'bell':
        a = s/2
        b = [1+a*A, -2*c, 1-a*A]
        d = [1+a/A, -2*c, 1-a/A]
    elif kind == 'low':
        k = 2*math.sqrt(A)*a
        b = [A*((A+1)-(A-1)*c+k), 2*A*((A-1)-(A+1)*c), A*((A+1)-(A-1)*c-k)]
        d = [(A+1)+(A-1)*c+k, -2*((A-1)+(A+1)*c), (A+1)+(A-1)*c-k]
    else:
        k = 2*math.sqrt(A)*a
        b = [A*((A+1)+(A-1)*c+k), -2*A*((A-1)+(A+1)*c), A*((A+1)+(A-1)*c-k)]
        d = [(A+1)-(A-1)*c+k, 2*((A-1)-(A+1)*c), (A+1)-(A-1)*c-k]
    return [x/d[0] for x in b+d[1:]]


class Filter:
    def __init__(self, c):
        self.c = c[:]
        self.target = c[:]
        self.state = [[0.]*4, [0.]*4]

    def tick(self, x, channel):
        b0,b1,b2,a1,a2 = self.c
        x1,x2,y1,y2 = self.state[channel]
        y = b0*x+b1*x1+b2*x2-a1*y1-a2*y2
        if not math.isfinite(y) or abs(y)>1e12:
            self.state[channel] = [0.]*4
            x1 = y1 = 0.
            y = 0
        if abs(y)<1e-30:
            y = 0.
        self.state[channel] = [x,x1,y,y1]
        return y


class Model:
    def __init__(self, sr=48000, **changes):
        self.sr = sr
        self.p = DEFAULT | changes
        self.alpha = 1-math.exp(-1/(.020*sr))
        self.step = 1/(.010*sr)
        self.filters = [Filter(c) for c in self.coefficients()]
        self.g = self.targets()

    def coefficients(self):
        p = self.p
        return [coeff('hp',p['hp'],0,self.sr), coeff('bell',p['pre_freq'],p['pre_gain'],self.sr),
                coeff('lp',p['lp'],0,self.sr), coeff('low',150,p['low'],self.sr),
                coeff('bell',p['mid_freq'],p['mid'],self.sr), coeff('high',4000,p['high'],self.sr)]

    def targets(self):
        p = self.p
        return dict(in_g=10**(p['input_db']/20), out_g=10**(p['output_db']/20), drive_g=p['drive'],
                    **{k:float(p[k]>=.5) for k in ('pre','dist','post','master','input','output')})

    def set(self, **changes):
        for key,value in changes.items():
            if key in RANGES:
                lo,hi = RANGES[key]
                value = max(lo,min(hi,value)) if not math.isnan(value) else lo
            self.p[key] = value
        for f,c in zip(self.filters,self.coefficients()):
            f.target = c

    def tick(self, left, right):
        t = self.targets()
        for key in self.g:
            delta = t[key]-self.g[key]
            self.g[key] += self.alpha*delta if key.endswith('_g') else max(-self.step,min(self.step,delta))
        for f in self.filters:
            f.c = [c+self.alpha*(t-c) for c,t in zip(f.c,f.target)]
        result = []
        for ch,x in enumerate((left,right)):
            dry = x if math.isfinite(x) and abs(x)<=1e12 else 0.
            g = self.g
            x = dry*(1+(g['in_g']-1)*g['input'])
            wet = x
            for f in self.filters[:3]:
                wet = f.tick(wet,ch)
            x += (wet-x)*g['pre']
            x += (math.tanh(g['drive_g']*x)-x)*g['dist']
            wet = x
            for f in self.filters[3:]:
                wet = f.tick(wet,ch)
            x += (wet-x)*g['post']
            x *= 1+(g['out_g']-1)*g['output']
            result.append(dry if g['master']==1 else x+(dry-x)*g['master'])
        return tuple(result)
