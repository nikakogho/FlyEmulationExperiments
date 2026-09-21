"""Opt-in reconstruction from empirical ERG bands, with explicit coverage.

Not an exact reproduction of the authors' unpublished joining code. Rh1 uses
their stated 0.5777 scale; Rh6 uses a declared least-squares overlap alignment.
No missing tails, absolute gains, or temporal physiology are inferred.
"""
from pathlib import Path
import json
import numpy as np
from .spectral import CHANNELS

SOURCE = Path(__file__).resolve().parents[1]/'research/calibration/sharkey2020_bands.json'


def overlap_scale(reference, candidate):
    a, b = np.asarray(reference, float), np.asarray(candidate, float)
    if a.ndim != 1 or a.shape != b.shape or len(a) < 2 or not np.isfinite([a, b]).all():
        raise ValueError('Expected paired finite overlap measurements')
    if np.any(a < 0) or np.any(b < 0) or b@b <= 0:
        raise ValueError('Invalid response amplitudes')
    return float((a@b)/(b@b))


def pooled_sd(mean_a, sd_a, mean_b, sd_b, n=6):
    """SD across two equal-size groups, including their different means.

    This is reconstructed between-animal spread, not a confidence interval;
    uncertainty in the fitted scale is not included.
    """
    return np.sqrt(((n-1)*(sd_a**2+sd_b**2)+n*(mean_a-mean_b)**2/2)/(2*n-1))


class CalibratedSpectralReceptors:
    def __init__(self, path=SOURCE):
        self.provenance = json.loads(Path(path).read_text())
        short, long = self.provenance['bands']
        self.curves, self.alignment = {}, {}
        for channel in CHANNELS:
            j = short['channels'].index(channel)
            w = np.array(short['wavelength_nm'], float)
            mean, sd = np.array(short['mean'])[:, j], np.array(short['sd'])[:, j]
            if channel in long['channels']:
                k = long['channels'].index(channel)
                lw = np.array(long['wavelength_nm'], float)
                lm, ls = np.array(long['mean'])[:, k], np.array(long['sd'])[:, k]
                overlap = np.intersect1d(w, lw)
                si, li = np.searchsorted(w, overlap), np.searchsorted(lw, overlap)
                scale = (self.provenance['rh1_long_scale_from_methods'] if channel == 'Rh1'
                         else overlap_scale(mean[si], lm[li]))
                a, b = mean[si].copy(), lm[li]*scale
                self.alignment[channel] = dict(scale=scale,
                    method='published fixed factor' if channel == 'Rh1' else 'least squares through origin, all 21 overlap wavelengths',
                    overlap_rmse=float(np.sqrt(np.mean((a-b)**2))),
                    overlap_relative_rmse=float(np.sqrt(np.mean((a-b)**2))/max(a)))
                sd[si] = pooled_sd(a, sd[si], b, ls[li]*scale, short['n'])
                mean[si] = (a+b)/2
                tail = lw > w[-1]
                w, mean, sd = np.r_[w, lw[tail]], np.r_[mean, lm[tail]*scale], np.r_[sd, ls[tail]*scale]
            if not (np.isfinite(mean).all() and np.isfinite(sd).all() and np.all(mean >= 0)
                    and np.all(sd >= 0) and np.all(np.diff(w) > 0) and mean.max() > 0):
                raise ValueError('Invalid measured response table')
            peak = float(mean.max())
            self.curves[channel] = dict(wavelength_nm=w, response=mean/peak,
                                        raw_mean=mean, raw_sd=sd, relative_sd=sd/peak)

    def excite(self, wavelength_nm, photon_radiance, channels=CHANNELS):
        """Relative ERG-shape proxy. Reject unsupported selected channels.

        To use 550-700 nm request Rh1/Rh6 explicitly. A whole retina cannot use
        that range until the other receptor tails are justified separately.
        """
        w, p = np.asarray(wavelength_nm, float), np.asarray(photon_radiance, float)
        channels = tuple(channels)
        if not channels or len(set(channels)) != len(channels) or any(c not in self.curves for c in channels):
            raise ValueError('Select known, distinct receptor channels')
        if w.ndim != 1 or len(w) < 2 or not np.isfinite(w).all() or np.any(np.diff(w) <= 0):
            raise ValueError('Expected increasing finite wavelengths')
        if p.ndim < 1 or p.shape[-1] != len(w) or not np.isfinite(p).all() or np.any(p < 0):
            raise ValueError('Expected nonnegative finite spectral radiance')
        response = []
        for c in channels:
            curve = self.curves[c]; cw = curve['wavelength_nm']
            if w[0] < cw[0] or w[-1] > cw[-1]:
                raise ValueError(f'{c} has measured support only {cw[0]:g}-{cw[-1]:g} nm')
            response.append(np.interp(w, cw, curve['response']))
        dx = np.diff(w)
        weights = np.r_[dx[0]/2, (dx[:-1]+dx[1:])/2, dx[-1]/2]
        # Match the legacy contiguous wavelength-by-channel layout so unchanged
        # curves also reproduce the same floating-point reduction order.
        return p @ (np.stack(response, axis=-1)*weights[:, None])
