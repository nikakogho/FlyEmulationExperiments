"""Algebraic fit to published probe displacement; no neural simulation."""
import numpy as np
from scipy.optimize import least_squares


def twitch(time_ms, amplitude_um, tau_ms, delay_ms):
    t=np.asarray(time_ms,dtype=float)
    if (not np.isfinite(t).all() or not np.isfinite([amplitude_um,tau_ms,delay_ms]).all()
            or amplitude_um<0 or tau_ms<=0 or delay_ms<0):
        raise ValueError('Invalid pulse parameters')
    u=np.maximum(t-delay_ms,0)/tau_ms
    return amplitude_um*u*u*np.exp(2-u)/4


def fit_twitch(time_ms, displacement_um):
    t=np.asarray(time_ms,dtype=float);y=np.asarray(displacement_um,dtype=float)
    if (t.ndim!=1 or t.shape!=y.shape or len(t)<8 or not np.isfinite(y).all()
            or not np.isfinite(t).all() or np.any(np.diff(t)<=0)):
        raise ValueError('Need matching finite ordered samples')
    fit=least_squares(lambda z:twitch(t,*z)-y,[4,8,5],bounds=([0,1,0],[10,40,10]))
    if not fit.success: raise ValueError('Fit did not converge')
    a,tau,delay=map(float,fit.x)
    return dict(amplitude_um=a,tau_ms=tau,delay_ms=delay,time_to_peak_ms=delay+2*tau,
                rmse_um=float(np.sqrt(np.mean(fit.fun**2))))
