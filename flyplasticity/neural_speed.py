"""Fixed engineering scalar readout; no direction, cue, location or reward input."""
import numpy as np

class NeuralSpeed:
    def __init__(self,n_outputs=2):
        self.n=n_outputs;self.rate_hz=0.
    def step(self,output_spikes):
        counts=np.asarray(output_spikes,dtype=float)
        if counts.shape!=(self.n,) or not np.isfinite(counts).all() or np.any(counts<0) or np.any(counts!=np.floor(counts)):
            raise ValueError('Invalid neural motor readout')
        decay=np.exp(-.005/.1)
        self.rate_hz=self.rate_hz*decay+(1-decay)*counts.mean()/.005
        speed=.35+.35*np.clip(self.rate_hz/160.,0,1)
        return np.full(2,speed)
