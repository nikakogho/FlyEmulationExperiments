"""Information boundary for the exploratory visual conditioning task.

Color features are engineered from eye-camera RGB pixels, not object labels.
This is not a recovered photoreceptor/optic-lobe model.
"""
import numpy as np


def visual_features(eye_images):
    pixels=np.asarray(eye_images,dtype=float)/255.
    if pixels.ndim!=4 or pixels.shape[0]!=2 or pixels.shape[-1]!=3:
        raise ValueError('Expected two RGB eye images')
    green=np.maximum(pixels[...,1]-np.maximum(pixels[...,0],pixels[...,2]),0)
    blue=np.maximum(pixels[...,2]-np.maximum(pixels[...,0],pixels[...,1]),0)
    return np.clip(30*np.stack([green.mean(axis=(1,2)),blue.mean(axis=(1,2))],axis=1),0,1)


def motor_output(mbon_rates, exploration):
    """Fixed avoidance readout. Receives no images, targets, rewards or positions."""
    left,right=np.asarray(mbon_rates,dtype=float)
    delta=np.clip(.8*(left-right)/max(left+right,10.)+exploration,-.3,.3)
    return np.array([1.+delta,1.-delta])


class LocalEligibilityLTD:
    def __init__(self, pre, pam, n_neurons, dt=.01, eta=4., tau_e=.1, tau_d=.05):
        self.pre=np.asarray(pre); self.pam=np.asarray(pam)
        self.dt,self.eta,self.tau_e,self.tau_d=dt,eta,tau_e,tau_d
        self.e=np.zeros(n_neurons); self.d=0.

    def step(self, counts, weights):
        self.e*=np.exp(-self.dt/self.tau_e)
        self.e[np.asarray(counts)>0]=1.
        rate=np.asarray(counts)[self.pam].mean()/self.dt
        drive=rate/60. if rate>=1 else 0.
        decay=np.exp(-self.dt/self.tau_d)
        self.d=self.d*decay+(1-decay)*drive
        return np.asarray(weights)*np.exp(-self.eta*self.dt*self.e[self.pre]*self.d)
