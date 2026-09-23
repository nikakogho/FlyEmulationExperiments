"""Offline sampling diagnostics, not a neural or transduction model."""
import numpy as np


def sampling_error(signal, stride):
    """Instantaneous subsampling + linear reconstruction on covered times only.

    The first axis is uniformly sampled time. This measures sampling loss; it
    does not fit a causal stimulus-response model or imply biological accuracy.
    """
    y = np.asarray(signal, dtype=float)
    if y.ndim != 1 or len(y) < 3 or not np.isfinite(y).all():
        raise ValueError('Expected a finite one-dimensional time series')
    if isinstance(stride, bool) or not isinstance(stride, (int, np.integer)) or stride < 1:
        raise ValueError('Stride must be a positive integer')
    indices = np.arange(0, len(y), stride)
    if len(indices) < 2:
        raise ValueError('At least two retained samples are required')
    stop = int(indices[-1])+1
    prediction = np.interp(np.arange(stop), indices, y[indices])
    rmse = float(np.sqrt(np.mean((prediction-y[:stop])**2)))
    scale = float(np.std(y[:stop]))
    return dict(rmse=rmse, normalized_rmse=rmse/scale if scale > 0 else 0.,
                covered_samples=stop, retained_samples=len(indices)), prediction


def optical_gain(time_s):
    """Synthetic positive 20/80 Hz optical test pattern; no neural exposure."""
    t = np.asarray(time_s, dtype=float)
    if not np.isfinite(t).all():
        raise ValueError('Nonfinite optical clock')
    return 1+.15*np.sin(2*np.pi*20*t)+.05*np.sin(2*np.pi*80*t)
