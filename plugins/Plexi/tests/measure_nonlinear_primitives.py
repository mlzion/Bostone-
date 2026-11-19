"""Memoryless diagnostics of original amp equations, not a tube-circuit model.
Requires NumPy for analysis only. Full amplifier measurements use REAPER.
"""
import argparse
import json
from pathlib import Path
import numpy as np
from measure_oversampling import spectrum


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--report',type=Path,required=True);a=p.parse_args();out=[]
    def rational(x):return x/(1+np.abs(x))
    def current(x):
        q=np.logaddexp(0,x);return q/(1+q)
    def branches(x):return np.tanh(2*x+.04)-np.tanh(.04),np.tanh(-1.9*x+.04)-np.tanh(.04)
    def power(x):
        pa,pb=branches(x);g=10**(3/20)
        return 2*(current(3*(g*pa-.1))-current(3*(g*pb-.1)))
    functions={
        'first-preamp':lambda x:np.tanh(.8*10**(6/20)*x+.22)-np.tanh(.22),
        'second-preamp':lambda x:rational(3*x+.1)-rational(.1),
        'phase-inverter-difference':lambda x:branches(x)[0]-branches(x)[1],
        'power-pair-unit-rail':power,
        'output-safety':lambda x:.8*np.tanh(x/.8)*10**(-12/20),
    }
    for rate in (44100,48000,96000):
        for hz in (200,1000,3000,6000,10000):
            n=8192;k=round(hz*n/rate);k+=int(k%2==0)
            for level in (.01,.1,.5):
                x=level*np.sin(2*np.pi*k*np.arange(n)/n)
                for name,f in functions.items():
                    s=dict(start=0,n=n,bin=k)
                    out.append(dict(stage=name,rate=rate,hz=k*rate/n,level=level,**spectrum(f(x),s)))
    a.report.write_text(json.dumps(out,indent=2)+'\n')


if __name__=='__main__':main()
