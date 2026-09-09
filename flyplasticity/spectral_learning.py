"""Explicit exploratory compression into five channels, never a reward label.

This adapter pools receptor subtypes spatially. It is suitable for a stationary
cue-memory diagnostic, not a claim of recovered visual projection physiology.
"""
import numpy as np


def receptor_features(actual, baseline, pale, gain=30.):
    actual, baseline = np.asarray(actual), np.asarray(baseline)
    pale = np.asarray(pale, dtype=bool)
    if (actual.shape != baseline.shape or actual.ndim != 3 or actual.shape[0] != 2
        or actual.shape[-1] != 3 or pale.shape != actual.shape[:2]
        or not np.isfinite(actual).all() or not np.isfinite(baseline).all()
        or np.any(actual < 0) or np.any(baseline < 0) or not np.isfinite(gain) or gain <= 0):
        raise ValueError('Invalid receptor data')
    delta = np.maximum(actual-baseline, 0)
    features = np.empty((2, 5))
    for eye in range(2):
        if pale[eye].all() or not pale[eye].any():
            raise ValueError('Both receptor subtypes required for this pooling diagnostic')
        features[eye] = [delta[eye, :, 0].mean(),
            delta[eye, pale[eye], 1].mean(), delta[eye, ~pale[eye], 1].mean(),
            delta[eye, pale[eye], 2].mean(), delta[eye, ~pale[eye], 2].mean()]
    return np.clip(gain*features, 0, 1)
