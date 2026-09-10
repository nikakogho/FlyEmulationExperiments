"""Geometry-aware engineering odor field and anatomical input transport.

Concentrations are normalized, not calibrated turbulent plumes or receptor Hz.
Only concentrations and acquisition time cross the neural-input interface.
"""
import numpy as np

SENSOR_NAMES=('LMaxillaryPalp_sensor','RMaxillaryPalp_sensor','LAntenna_sensor','RAntenna_sensor')

class OdorField:
    def __init__(self,sources,peaks=None,sigma_mm=6.):
        self.sources=np.asarray(sources,dtype=float).copy()
        self.peaks=np.eye(len(self.sources)) if peaks is None else np.asarray(peaks,dtype=float).copy()
        self.sigma=float(sigma_mm)
        if (self.sources.ndim!=2 or self.sources.shape[1]!=3 or self.peaks.ndim!=2
                or self.peaks.shape[0]!=len(self.sources) or not np.isfinite(self.sources).all()
                or not np.isfinite(self.peaks).all() or np.any(self.peaks<0)
                or not np.isfinite(self.sigma) or self.sigma<=0):raise ValueError('Invalid odor field')

    def sample(self,positions):
        p=np.asarray(positions,dtype=float)
        if p.ndim!=2 or p.shape[1]!=3 or not np.isfinite(p).all():raise ValueError('Invalid sensor geometry')
        d2=((p[None,:,:]-self.sources[:,None,:])**2).sum(axis=2)
        return self.peaks.T@np.exp(-d2/(2*self.sigma**2))

class OrnTransport:
    def __init__(self,channels,sides,nerves,max_age_s=.005):
        self.channels=np.asarray(channels,dtype=int)
        self.sides=tuple(sides);self.nerves=tuple(nerves);self.max_age=max_age_s
        if (self.channels.ndim!=1 or len(self.sides)!=len(self.channels) or len(self.nerves)!=len(self.channels)
                or np.any(self.channels<0) or np.any(self.channels>1)
                or any(s not in ('left','right','na') for s in self.sides)
                or any(n not in ('AN','MxLbN') for n in self.nerves)):
            raise ValueError('Unmapped sensory anatomy')
        self.unknown_sides=sum(s=='na' for s in self.sides)
        self.last=None

    def rates(self,concentrations,sample_time_s,neural_time_s):
        c=np.asarray(concentrations,dtype=float)
        if (c.shape!=(2,4) or not np.isfinite(c).all() or np.any(c<0) or np.any(c>1)
                or not np.isfinite([sample_time_s,neural_time_s]).all()
                or min(sample_time_s,neural_time_s)<0
                or neural_time_s<sample_time_s or neural_time_s-sample_time_s>self.max_age+1e-12
                or self.last is not None and sample_time_s<=self.last):
            raise ValueError('Invalid or stale sensory sample')
        out=[]
        for channel,side,nerve in zip(self.channels,self.sides,self.nerves):
            indices=(2,3) if nerve=='AN' else (0,1)
            # Explicit symmetric approximation for unknown side, never invented laterality.
            value=c[channel,list(indices)].mean() if side=='na' else c[channel,indices[side=='right']]
            out.append(500.*value)
        self.last=sample_time_s
        return np.asarray(out)

def make_arena():
    from flygym.arena import OdorArena
    sources=np.array([[8.,4.,1.],[8.,-4.,1.]])
    arena=OdorArena(odor_source=sources,peak_odor_intensity=np.eye(2),
                    diffuse_func=lambda distance:np.exp(-distance**2/72.),
                    marker_colors=[(.15,.65,.85,1),(.95,.65,.15,1)],marker_size=.4)
    # Markers visualize sources; they are not physical obstacles or contact rewards.
    for geom in arena.root_element.find_all('geom'):
        if 'odor_source_marker' in str(getattr(geom.parent,'name','')):geom.contype=0;geom.conaffinity=0
    return arena,OdorField(sources)
