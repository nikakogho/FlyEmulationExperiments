"""Explicit spectra -> empirical receptor excitation, with no RGB conversion.

Radiance is relative photon spectral radiance per nm. Response curves are
normalized ERG shapes, so the output is a relative proxy, not measured voltage.
"""
from pathlib import Path
import numpy as np
from scipy.integrate import trapezoid

CHANNELS = ('Rh1', 'Rh3', 'Rh4', 'Rh5', 'Rh6')


def fisheye_channels(image, zoom, distortion_coefficient):
    """FlyGym's spatial remap, preserving arbitrary floating-point channels."""
    image = np.asarray(image)
    nr, nc = image.shape[:2]
    r, c = np.indices((nr, nc))
    rn, cn = (2*r-nr)/nr/zoom, (2*c-nc)/nc/zoom
    denom = 1-distortion_coefficient*(rn*rn+cn*cn)+1e-6
    sr = (((rn/denom+1)*nr)/2).astype(int)
    sc = (((cn/denom+1)*nc)/2).astype(int)
    valid = (sr >= 0) & (sr < nr) & (sc >= 0) & (sc < nc)
    result = np.zeros_like(image)
    result[valid] = image[sr[valid], sc[valid]]
    return result


class SpectralReceptors:
    def __init__(self, path=None):
        path = path or Path(__file__).resolve().parents[1] / 'data/spectral/receptor_curves.npz'
        with np.load(path) as data:
            self.wavelength_nm = data['wavelength_nm'].copy()
            self.response = data['response'].copy()
        if self.response.shape != (len(self.wavelength_nm), 5) or not np.isfinite(self.response).all():
            raise ValueError('Invalid spectral response table')

    def excite(self, wavelength_nm, photon_radiance):
        w = np.asarray(wavelength_nm, dtype=float)
        p = np.asarray(photon_radiance, dtype=float)
        if (w.ndim != 1 or len(w) < 2 or not np.isfinite(w).all() or
            np.any(np.diff(w) <= 0) or w[0] < self.wavelength_nm[0] or w[-1] > self.wavelength_nm[-1]):
            raise ValueError('Wavelengths must increase within measured support 315-550 nm')
        if p.ndim < 1 or p.shape[-1] != len(w) or not np.isfinite(p).all() or np.any(p < 0):
            raise ValueError('Expected nonnegative finite photon spectral radiance')
        response = np.stack([np.interp(w, self.wavelength_nm, c) for c in self.response.T], axis=-1)
        # Explicit trapezoidal quadrature accommodates nonuniform spectral grids.
        dx = np.diff(w)
        weights = np.r_[dx[0]/2, (dx[:-1]+dx[1:])/2, dx[-1]/2]
        return p @ (response * weights[:, None])


def narrowband(wavelength_nm, center_nm, sigma_nm=5., total_photons=1.):
    w = np.asarray(wavelength_nm, dtype=float)
    if (w.ndim != 1 or len(w) < 2 or not np.isfinite(w).all() or np.any(np.diff(w) <= 0)
        or not np.isfinite([center_nm, sigma_nm, total_photons]).all()
        or sigma_nm <= 0 or total_photons < 0 or center_nm < w[0] or center_nm > w[-1]):
        raise ValueError('Invalid narrowband emitter')
    p = np.exp(-.5 * ((w-center_nm)/sigma_nm)**2)
    return p * total_photons / trapezoid(p, w)


class SpectralRetina:
    """One broad outer response and one R7/R8 pair per ommatidium.

    A seeded 30% pale mosaic is a population approximation, not the recorded
    fly's actual mosaic. Dorsal rim specializations are not modeled.
    """
    def __init__(self, bridge, seed=0, pale_fraction=.3):
        if not 0 < pale_fraction < 1:
            raise ValueError('Pale fraction must be between zero and one')
        self.bridge = bridge
        self.receptors = SpectralReceptors()
        self.pale = np.random.default_rng(seed).random((2, len(bridge.counts))) < pale_fraction

    def sample_excitation(self, image):
        """Sample five potential receptor responses; select actual mosaic pair."""
        b = self.bridge
        image = np.asarray(image, dtype=float)
        if image.shape != (2, *b.ids.shape, 5) or not np.isfinite(image).all() or np.any(image < 0):
            raise ValueError('Expected five nonnegative spectral responses at each eye pixel')
        all_types = np.empty((2, len(b.counts), 5))
        for eye in range(2):
            for c in range(5):
                all_types[eye, :, c] = np.bincount(b.ids.ravel(), weights=image[eye, ..., c].ravel(),
                    minlength=len(b.counts)+1)[1:] / b.counts
        all_types = all_types[:, b.to_target]
        actual = np.stack([all_types[..., 0],
            np.where(self.pale, all_types[..., 1], all_types[..., 2]),
            np.where(self.pale, all_types[..., 3], all_types[..., 4])], axis=-1)
        return actual, all_types


def render_spectral_eyes(physics, camera_names, image_shape, geom_spectra, sky_spectrum, receptors):
    """MuJoCo visibility plus explicit surface radiance spectra.

    All opaque surfaces must be assigned. This is an emissive/uniform-radiance
    scene approximation, without interreflection or wavelength-dependent optics.
    Geometry IDs remain inside the renderer; only excitation images leave it.
    """
    if set(geom_spectra) != set(range(physics.model.ngeom)):
        raise ValueError('Every scene geometry needs an explicit spectrum')
    w = receptors.wavelength_nm
    lookup = receptors.excite(w, np.array([geom_spectra[i] for i in range(physics.model.ngeom)]))
    sky = receptors.excite(w, sky_spectrum)
    images = []
    for camera in camera_names:
        seg = physics.render(height=image_shape[0], width=image_shape[1], camera_id=camera, segmentation=True)
        # dm_control segmentation channels are object ID, object type; mjOBJ_GEOM=5.
        valid = (seg[..., 1] == 5) & (seg[..., 0] >= 0)
        result = np.broadcast_to(sky, (*image_shape, 5)).copy()
        result[valid] = lookup[seg[..., 0][valid]]
        images.append(result)
    return np.array(images)
