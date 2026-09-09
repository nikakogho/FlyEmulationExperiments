"""Offline recorded-signal analysis. No neural state or actuator commands."""
import numpy as np
from scipy.optimize import least_squares
from .figure_twitch import twitch


def recording_time(params, sample_count):
    fs = float(params['sampratein'])
    if not np.isfinite(fs) or fs <= 0 or sample_count != round(float(params['durSweep']) * fs):
        raise ValueError('Invalid acquisition duration or sample rate')
    return np.arange(sample_count) / fs - float(params.get('preDurInSec', 0))


def frame_indices(exposure, frame_count):
    """Port raw TTL branch of author's postHocExposure, including end edges.

    Supports raw square-wave TTL only; rejects ambiguity instead of inventing
    timestamps. Author inserts isolated missing exposures and trims trailing ones.
    """
    e = np.asarray(exposure)
    if e.ndim != 1 or not np.isfinite(e).all() or not np.isin(e, [0, 1]).all():
        raise ValueError('Expected finite binary exposure vector')
    if frame_count < 2 or e[:2].sum() == 0:
        raise ValueError('Unexpected exposure start or frame count')
    ends = np.flatnonzero((e[:-1] == 1) & (e[1:] == 0))
    gaps = np.diff(ends)
    if len(gaps) < 2:
        raise ValueError('Too few exposure edges')
    vals, counts = np.unique(gaps, return_counts=True)
    period = int(vals[np.argmax(counts)])
    if period < 2:
        raise ValueError('Unsupported processed exposure representation')
    missed = np.flatnonzero((gaps > 1.95 * period) & (gaps < 2.05 * period))
    missed = missed[missed != 0]  # author excludes delayed second exposure
    ends = np.sort(np.r_[ends, ends[missed] + period])
    if len(ends) < frame_count or np.any(np.diff(ends) > 2.05 * period):
        raise ValueError('Unrecoverable exposure/frame mismatch')
    return ends[:frame_count], {'inserted_frames': len(missed),
                               'trimmed_trailing_exposures': len(ends) - frame_count,
                               'modal_period_samples': period}


def matlab_spike_indices(spikes, sample_count):
    s = np.atleast_1d(np.asarray(spikes, dtype=float))
    if s.ndim != 1 or not np.isfinite(s).all() or np.any(s != np.floor(s)):
        raise ValueError('Invalid MATLAB spike indices')
    s = s.astype(int) - 1
    if np.any(s < 0) or np.any(s >= sample_count) or np.any(np.diff(s) <= 0):
        raise ValueError('Spike indices out of bounds or unordered')
    return s


def passive_pulse(current_pa, voltage_mv, fs):
    i, v = np.asarray(current_pa), np.asarray(voltage_mv)
    if i.ndim != 1 or i.shape != v.shape or not np.isfinite(i).all() or not np.isfinite(v).all():
        raise ValueError('Invalid current/voltage samples')
    if not np.isfinite(fs) or fs <= 0 or len(i) / fs <= .11:
        raise ValueError('Missing calibration pulse interval')
    t = np.arange(len(i)) / fs
    di = i[(t > .01) & (t < .06)].mean() - i[(t > .06) & (t < .11)].mean()
    dv = v[(t > .04) & (t < .06)].mean() - v[(t > .09) & (t < .11)].mean()
    if not -10 <= di <= -1:
        raise ValueError('Not the expected small hyperpolarizing pulse')
    return {'delta_current_pa': float(di), 'delta_voltage_mv': float(dv),
            'resistance_mohm': float(1000 * dv / di)}


def aligned_probe(trial, um_per_pixel=np.sqrt(1.03)):
    com = np.asarray(trial['forceProbeStuff']['CoM'], dtype=float)
    if com.ndim != 1 or not np.isfinite(com).all() or not np.isfinite(um_per_pixel) or um_per_pixel <= 0:
        raise ValueError('Invalid probe trace or scale')
    # Verify stored evaluation points are one image pixel apart, not micrometres.
    points = np.asarray(trial['forceProbeStuff']['EvalPnts'])
    if points.ndim != 2 or points.shape[0] != 2 or not np.allclose(np.linalg.norm(np.diff(points, axis=1), axis=0), 1):
        raise ValueError('Unexpected probe coordinate scale')
    t = recording_time(trial['params'], len(trial['voltage_1']))
    spikes = matlab_spike_indices(trial.get('spikes', []), len(t))
    if len(spikes) != 1:
        raise ValueError('Requires exactly one recorded spike')
    idx, audit = frame_indices(trial['exposure'], len(com))
    ft = t[idx] - t[spikes[0]]
    baseline = com[ft < 0][-4:]
    if len(baseline) != 4:
        raise ValueError('Insufficient pre-spike baseline')
    selection = (ft >= -.02) & (ft <= .12)
    if ft[-1] < .12 or selection.sum() < 8:
        raise ValueError('Incomplete response window')
    return ft[selection] * 1000, (com[selection] - baseline.mean()) * um_per_pixel, audit


def fit_probe_trials(traces):
    """Equal weight per trial; fixed model/bounds, no held-out data input."""
    if len(traces) < 3:
        raise ValueError('Need at least three training trials')
    for t, y in traces:
        if len(t) < 8 or np.shape(t) != np.shape(y) or not np.isfinite(t).all() or not np.isfinite(y).all() or np.any(np.diff(t) <= 0):
            raise ValueError('Invalid fit samples')
    def residual(z):
        return np.concatenate([(twitch(t, *z) - y) / np.sqrt(len(t)) for t, y in traces])
    low = np.array([0., 1., 0.]); high = np.array([50., 40., 10.])
    fit = least_squares(residual, [4., 8., 5.], bounds=(low, high))
    if not fit.success:
        raise ValueError('Probe fit failed')
    a, tau, delay = map(float, fit.x)
    return {'amplitude_um': a, 'tau_ms': tau, 'delay_ms': delay,
            'time_to_peak_ms': delay + 2 * tau,
            'parameter_at_bound': bool(np.any(np.minimum(fit.x-low, high-fit.x) < 1e-4))}
