"""Validated peripheral snapshots. No neural model, reward or target interface."""
from dataclasses import dataclass
import numpy as np


def snapshot(value):
    result = np.array(value, dtype=float, copy=True)
    if not np.isfinite(result).all():
        raise ValueError('Nonfinite sensory observation')
    result.setflags(write=False)
    return result


@dataclass(frozen=True)
class SpectralBodyFrame:
    time_s: float
    acquisition_s: np.ndarray  # eye, joints, contacts, odor; all acquired explicitly
    eye_excitation: np.ndarray  # two eyes, ommatidia, outer/R7/R8
    joint_angles_rad: np.ndarray
    joint_velocities_rad_s: np.ndarray
    contact_vectors_native: np.ndarray  # FlyGym mechanical units, not receptor Hz
    odor_concentration: np.ndarray  # tracer, L/R palps and L/R antennae
    previous_command: np.ndarray
    unavailable: tuple = ('taste', 'wind_receptors', 'hearing', 'temperature_receptors',
                          'humidity_receptors', 'ocelli', 'neural_proprioception')


class SpectralBodyStream:
    def __init__(self, sample_interval_s=.01):
        if not np.isfinite(sample_interval_s) or sample_interval_s <= 0:
            raise ValueError('Invalid sample interval')
        self.interval = sample_interval_s
        self.last = None
        self.layout = None

    def update(self, *, time_s, acquisition_s, eye_excitation, joint_angles_rad,
               joint_velocities_rad_s, contact_vectors_native, odor_concentration,
               previous_command):
        t = float(time_s)
        a, eye, q, v, force, odor, u = map(snapshot, (acquisition_s, eye_excitation,
            joint_angles_rad, joint_velocities_rad_s, contact_vectors_native,
            odor_concentration, previous_command))
        if not np.isfinite(t) or t < 0 or a.shape != (4,) or not np.allclose(a, t, atol=1e-9, rtol=0):
            raise ValueError('Missing, future or stale acquisition')
        if self.last is None and abs(t) > 1e-9:
            raise ValueError('Recording must begin at zero')
        if self.last is not None and abs(t-self.last-self.interval) > 1e-8:
            raise ValueError('Discontinuous sensory recording')
        if (eye.ndim != 3 or eye.shape[0] != 2 or eye.shape[1] < 1 or eye.shape[2] != 3
            or np.any(eye < 0) or q.ndim != 1 or not q.size or v.shape != q.shape
            or force.ndim != 2 or force.shape[1] != 3 or not len(force)
            or odor.ndim != 2 or odor.shape[1] != 4 or not len(odor)
            or np.any(odor < 0) or np.any(odor > 1)
            or u.shape != (2,) or np.any(u < 0) or np.any(u > 1)):
            raise ValueError('Invalid peripheral layout or range')
        layout = (eye.shape, q.shape, force.shape, odor.shape)
        if self.layout is not None and self.layout != layout:
            raise ValueError('Sensor layout changed')
        self.last, self.layout = t, layout
        return SpectralBodyFrame(t, a, eye, q, v, force, odor, u)


def project_world(point, camera_position, camera_rotation, fovy_deg, image_shape):
    """Independent pinhole projection in MuJoCo camera coordinates, pixel centers."""
    p, c, r = map(np.asarray, (point, camera_position, camera_rotation))
    if p.shape != (3,) or c.shape != (3,) or r.shape != (3, 3):
        raise ValueError('Invalid camera geometry')
    if not np.isfinite(np.r_[p, c, r.ravel(), fovy_deg]).all() or not 0 < fovy_deg < 180:
        raise ValueError('Invalid camera values')
    local = r.T @ (p-c)
    if local[2] >= 0:
        raise ValueError('Target behind camera')
    h, w = image_shape
    focal = h/(2*np.tan(np.deg2rad(fovy_deg)/2))
    return np.array([(h-1)/2-focal*local[1]/-local[2],
                     (w-1)/2+focal*local[0]/-local[2]])


def scheduled_command(t):
    """Mechanical fixture only; no sensory dependence, reward or learning."""
    if not np.isfinite(t) or t < 0:
        raise ValueError('Invalid fixture time')
    if .3 <= t < 1.1 or 1.6 <= t < 2.1:
        return np.array([.6, .6])
    if 1.1 <= t < 1.6:
        return np.array([.45, .75])
    return np.zeros(2)
