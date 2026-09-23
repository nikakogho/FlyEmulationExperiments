"""Static input transformations for offline signal regression only."""
import numpy as np


def transform_light(values, kind, parameter=1.):
    """Monotone transforms in stored source units, without clipping or adaptation."""
    x = np.asarray(values, dtype=float)
    if x.ndim != 1 or not np.isfinite(x).all():
        raise ValueError('Expected finite one-dimensional recorded light signal')
    if not np.isfinite(parameter) or parameter <= 0:
        raise ValueError('Transformation parameter must be positive and finite')
    if kind == 'identity':
        if parameter != 1.:
            raise ValueError('Identity parameter must be one')
        result = x.copy()
    elif kind == 'signed_power':
        result = np.sign(x)*np.abs(x)**parameter
    elif kind == 'signed_log1p':
        result = np.sign(x)*np.log1p(np.abs(x)/parameter)
    else:
        raise ValueError('Unknown light transformation')
    if not np.isfinite(result).all():
        raise ValueError('Nonfinite transformed input')
    return result
