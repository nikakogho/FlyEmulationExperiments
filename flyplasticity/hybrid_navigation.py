"""Fixed, explicitly engineered navigation using a reduced population readout.

Eight sinusoidal heading channels and a directional population product are
inspired by Matheson et al. 2022. This algebraic controller is NOT a validated
PFL/hDelta circuit or a port of its recurrent neural model. No goal coordinate,
odor identity or reward label crosses the controller interface.
"""
import numpy as np


def population_turn(heading,upwind):
    if not np.isfinite([heading,upwind]).all():raise ValueError('Missing orientation')
    phase=np.arange(8)*2*np.pi/8
    goal=(1+np.cos(phase-upwind))/2
    left=(1+np.cos(phase-heading-np.pi/2))/2
    right=(1+np.cos(phase-heading+np.pi/2))/2
    return float(4/8*(goal@left-goal@right))


class HybridNavigation:
    def __init__(self):self.rate_hz=0.

    def step(self,output_spikes,heading,wind_world,odor_load):
        counts=np.asarray(output_spikes,dtype=float);wind=np.asarray(wind_world,dtype=float)
        if (counts.shape!=(2,) or wind.shape!=(2,) or not np.isfinite(np.r_[counts,wind,heading,odor_load]).all()
            or not 0<=odor_load<=2
            or np.any(counts<0) or np.any(counts!=np.floor(counts))):raise ValueError('Invalid motor input')
        decay=np.exp(-.005/.1)
        self.rate_hz=decay*self.rate_hz+(1-decay)*counts.mean()/.005
        # Explicit inhibitory-output hypothesis: lower MBON01 response permits
        # stronger approach. Total odor presence gates locomotion, never identity.
        if odor_load<.05:return np.zeros(2)
        speed=(.95-.45*min(self.rate_hz/300.,1.))*min(odor_load/.2,1.)
        turn=0. if np.linalg.norm(wind)<1e-8 else population_turn(heading,np.arctan2(-wind[1],-wind[0]))
        gain=.4*(.5+.5*80/(80+self.rate_hz))
        return np.clip(speed*np.array([1-gain*turn,1+gain*turn]),0,.95)


class PreferenceField:
    """Two identical weak radial airflow sources, carrying distinct odors.

    Analytic environment, not CFD or calibrated receptor transduction. Gradients
    are supplied ONLY to the behavioral auditor, never to the controller.
    """
    def __init__(self,sources,swapped=False):
        self.sources=np.asarray(sources,dtype=float).copy();self.sigma=4.
        if self.sources.shape!=(2,3) or not np.isfinite(self.sources).all():raise ValueError('Invalid sources')
        self.order=np.array([1,0] if swapped else [0,1])

    def sample(self,sites):
        p=np.asarray(sites,dtype=float)
        if p.ndim!=2 or p.shape[1]!=3 or not np.isfinite(p).all():raise ValueError('Invalid sites')
        delta=p[None,:,:]-self.sources[:,None,:]
        return np.exp(-np.sum(delta*delta,axis=2)/(2*self.sigma**2))[self.order]

    def gradients(self,point):
        p=np.asarray(point,dtype=float)
        c=self.sample(p[None,:])[:,0]
        return -(p-self.sources[self.order])*c[:,None]/self.sigma**2

    def wind(self,point):
        p=np.asarray(point,dtype=float)
        if p.shape!=(3,) or not np.isfinite(p).all():raise ValueError('Invalid wind site')
        d=p[:2]-self.sources[:,:2];radius=np.linalg.norm(d,axis=1)
        return np.sum(d/(1+radius[:,None])*np.exp(-radius[:,None]**2/72),axis=0)
