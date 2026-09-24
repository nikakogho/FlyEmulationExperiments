"""Offline causal regressors with linear and compressed source-signal paths."""
import numpy as np
from flyplasticity.causal_filter import causal_rows
from flyplasticity.nonlinear_filter import transform_light


def path_rows(signal, kind, lag=80):
    raw = causal_rows(signal, lag)
    if kind == 'linear':
        return raw
    compressed = causal_rows(transform_light(signal, 'signed_log1p', .5), lag)
    if kind == 'compressed':
        return compressed
    if kind == 'combined':
        return np.concatenate([raw, compressed], axis=1)
    raise ValueError('Unknown path configuration')
