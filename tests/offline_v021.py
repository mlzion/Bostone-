"""v0.2 reference processing with only v0.2.1's three target ranges changed.
This numerical model does not interpret or compile JSFX/EEL2.
"""
import math
from offline_v02 import V02, V02_RANGES

V021_RANGES=V02_RANGES | dict(hp=(40,1000),pre_freq=(150,2000),lp=(400,10000))


class V021(V02):
    def set(self,**changes):
        for key,value in changes.items():
            if key in V021_RANGES:
                lo,hi=V021_RANGES[key]
                value=max(lo,min(hi,value)) if not math.isnan(value) else lo
            self.p[key]=value
        for f,c in zip(self.filters,self.coefficients()):
            f.target=c
