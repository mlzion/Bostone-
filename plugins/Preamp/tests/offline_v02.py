"""Independent v0.2 numerical reference; does not execute EEL2."""
import math
from offline_dsp import Model, Filter, coeff, RANGES

EXTRA = dict(pre_mode=0, bp_freq=685, bp_q=1, bp_level=0,
             drive_mode=0, stage_db=12, intercut=6000, trim_db=0)
V02_RANGES = RANGES | dict(lp=(400,15000), bp_freq=(150,4000), bp_q=(.25,4),
                          bp_level=(-12,12), stage_db=(0,18), intercut=(800,12000), trim_db=(-12,12))


def band_coeff(f, q, sr):
    w = 2*math.pi*min(.45*sr,max(10,f))/sr
    a = math.sin(w)/(2*q)
    return [a/(1+a),0,-a/(1+a),-2*math.cos(w)/(1+a),(1-a)/(1+a)]


class V02(Model):
    def __init__(self, sr=48000, **changes):
        super().__init__(sr, **(EXTRA | changes))

    def coefficients(self):
        p = self.p
        return super().coefficients()+[band_coeff(p['bp_freq'],p['bp_q'],self.sr),
                                      coeff('lp',p['intercut'],0,self.sr)]

    def targets(self):
        p = self.p
        return super().targets() | dict(band=float(p['pre_mode']>=.5),strong=float(p['drive_mode']>=.5),
                                       band_level_g=10**(p['bp_level']/20),stage_g=10**(p['stage_db']/20),
                                       trim_g=10**(p['trim_db']/20))

    def set(self, **changes):
        for key,value in changes.items():
            if key in V02_RANGES:
                lo,hi = V02_RANGES[key]
                value = max(lo,min(hi,value)) if not math.isnan(value) else lo
            self.p[key] = value
        for f,c in zip(self.filters,self.coefficients()):
            f.target = c

    def tick(self, left, right):
        t = self.targets()
        for key in self.g:
            delta=t[key]-self.g[key]
            self.g[key] += self.alpha*delta if key.endswith('_g') else max(-self.step,min(self.step,delta))
        for f in self.filters:
            f.c = [c+self.alpha*(t-c) for c,t in zip(f.c,f.target)]
        result=[]
        for ch,x in enumerate((left,right)):
            dry=x if math.isfinite(x) and abs(x)<=1e12 else 0.
            g=self.g
            x=dry*(1+(g['in_g']-1)*g['input'])
            wet=x
            for f in self.filters[:3]: wet=f.tick(wet,ch)
            band=self.filters[6].tick(x,ch)*g['band_level_g']
            if g['band']>0: wet += (band-wet)*g['band']
            x += (wet-x)*g['pre']
            legacy=math.tanh(g['drive_g']*x)
            strong=math.tanh(g['stage_g']*self.filters[7].tick(legacy,ch))*g['trim_g']/math.sqrt(g['stage_g'])
            clip=legacy
            if g['strong']>0: clip += (strong-clip)*g['strong']
            x += (clip-x)*g['dist']
            wet=x
            for f in self.filters[3:6]: wet=f.tick(wet,ch)
            x += (wet-x)*g['post']
            x *= 1+(g['out_g']-1)*g['output']
            result.append(dry if g['master']==1 else x+(dry-x)*g['master'])
        return tuple(result)
