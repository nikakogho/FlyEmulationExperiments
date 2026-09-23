"""Offline linear signal-processing benchmark, disconnected from neural code."""
from dataclasses import dataclass
import numpy as np


def causal_rows(stimulus, max_lag):
    """Rows are [x(t), x(t-1), ..., x(t-max_lag)]; no padding or wrap."""
    x = np.asarray(stimulus, dtype=float)
    if (x.ndim != 1 or not np.isfinite(x).all() or isinstance(max_lag, bool)
            or not isinstance(max_lag, (int, np.integer))
            or not 0 <= max_lag < len(x)):
        raise ValueError('Invalid causal input or lag')
    return np.lib.stride_tricks.sliding_window_view(x, max_lag+1)[:, ::-1].copy()


@dataclass(frozen=True)
class LinearFilter:
    weights: np.ndarray
    intercept: float

    def predict(self, rows):
        x = np.asarray(rows, dtype=float)
        if x.ndim != 2 or x.shape[1] != len(self.weights) or not np.isfinite(x).all():
            raise ValueError('Invalid prediction rows')
        return x @ self.weights + self.intercept


def fit_ridge(rows, target, penalty):
    """Training-only centering/scaling; mean squared loss + penalty*||w||^2."""
    x, y = np.asarray(rows, dtype=float), np.asarray(target, dtype=float)
    if (x.ndim != 2 or y.shape != (len(x),) or len(x) < 2 or x.shape[1] < 1
            or not np.isfinite(x).all() or not np.isfinite(y).all()
            or not np.isfinite(penalty) or penalty < 0):
        raise ValueError('Invalid fit data or penalty')
    xm, ym = x.mean(axis=0), float(y.mean())
    scale = float(np.sqrt(np.mean((x-xm)**2)))
    if scale == 0:
        raise ValueError('Stimulus has no variation')
    z = (x-xm)/scale
    w = np.linalg.solve(z.T @ z / len(x) + penalty*np.eye(x.shape[1]),
                        z.T @ (y-ym) / len(x)) / scale
    return LinearFilter(w, float(ym-xm @ w))


def prediction_error(target, prediction):
    y, p = np.asarray(target, dtype=float), np.asarray(prediction, dtype=float)
    if (y.ndim != 1 or p.shape != y.shape or len(y) < 2
            or not np.isfinite(y).all() or not np.isfinite(p).all()
            or np.std(y) == 0):
        raise ValueError('Invalid prediction comparison')
    mse = float(np.mean((y-p)**2))
    variance = float(np.var(y))
    return dict(rmse_mV=float(np.sqrt(mse)), normalized_rmse=float(np.sqrt(mse/variance)),
                r_squared=1-mse/variance, samples=len(y))
