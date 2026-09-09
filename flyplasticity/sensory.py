"""Timestamped sensory transport, not a neural or receptor model.

Preserves retinal space and separates unavailable/stale information from zero.
No scene coordinates, food labels, rewards or target directions enter this API.
"""
from dataclasses import dataclass
import numpy as np


def _snapshot(value):
    result=np.array(value,dtype=np.float64,copy=True)
    if not np.isfinite(result).all(): raise ValueError('Non-finite sensory value')
    result.setflags(write=False)
    return result


@dataclass(frozen=True)
class SensoryFrame:
    time_s: float
    vision_time_s: float
    vision_fresh: bool
    rgb: np.ndarray
    luminance: np.ndarray
    temporal_contrast_per_s: np.ndarray | None
    joint_angles_rad: np.ndarray
    joint_velocities_rad_s: np.ndarray
    contact_load_native_units: np.ndarray
    previous_motor_command: np.ndarray
    # Unimplemented modalities are absent, never fabricated quiet measurements.
    unavailable_modalities: tuple = ('odor','taste','airflow','audition','internal_physiology')


class SensoryStream:
    def __init__(self, max_vision_age_s=.03, max_vision_gap_s=.05):
        if min(max_vision_age_s,max_vision_gap_s)<=0:
            raise ValueError('Timing limits must be positive')
        self.max_age=max_vision_age_s; self.max_gap=max_vision_gap_s
        self.reset()

    def reset(self):
        self._time=None; self._vision_time=None; self._rgb=None
        self._luminance=None; self._body_shapes=None

    def update(self, *, time_s, vision_time_s, eye_rgb, joint_angles_rad,
               joint_velocities_rad_s, contact_forces, previous_motor_command):
        time_s=float(time_s); vision_time_s=float(vision_time_s)
        if not np.isfinite([time_s,vision_time_s]).all() or min(time_s,vision_time_s)<0:
            raise ValueError('Bad timestamp')
        if self._time is not None and time_s<=self._time:
            raise ValueError('Time must advance; call reset for a new episode')
        if vision_time_s>time_s+1e-10 or time_s-vision_time_s>self.max_age+1e-10:
            raise ValueError('Future or stale vision')
        rgb=_snapshot(eye_rgb)
        if rgb.ndim!=4 or rgb.shape[0]!=2 or rgb.shape[-1]!=3 or min(rgb.shape[1:3])<2:
            raise ValueError('Expected two RGB images')
        if rgb.min()<0 or rgb.max()>255: raise ValueError('RGB must be in 0..255')
        rgb=_snapshot(rgb/255.)
        # Engineering luminance proxy, not calibrated Drosophila spectral tuning.
        luminance=_snapshot(rgb @ np.array([.2126,.7152,.0722]))
        angles=_snapshot(joint_angles_rad); velocity=_snapshot(joint_velocities_rad_s)
        forces=_snapshot(contact_forces); motor=_snapshot(previous_motor_command)
        if angles.ndim!=1 or not angles.size or velocity.shape!=angles.shape:
            raise ValueError('Joint angle/velocity shapes disagree')
        if forces.ndim!=2 or forces.shape[1]!=3 or not len(forces):
            raise ValueError('Expected contact-force vectors')
        if motor.shape!=(2,) or np.any(motor<0) or np.any(motor>1.3):
            raise ValueError('Bad previous motor command')
        shapes=(angles.shape,forces.shape)
        if self._body_shapes is not None and shapes!=self._body_shapes:
            raise ValueError('Sensor layout changed without reset')
        fresh=self._vision_time is None or vision_time_s>self._vision_time
        contrast=None
        if self._vision_time is not None:
            if rgb.shape!=self._rgb.shape: raise ValueError('Retina shape changed without reset')
            gap=vision_time_s-self._vision_time
            if gap<0 or gap>self.max_gap+1e-10: raise ValueError('Discontinuous vision timestamps')
            if not fresh and not np.array_equal(rgb,self._rgb):
                raise ValueError('Image changed with unchanged image timestamp')
            if fresh:
                contrast=_snapshot((luminance-self._luminance)/gap)
        # Commit history only after all validation succeeds.
        self._time=time_s; self._body_shapes=shapes
        if fresh:
            self._vision_time=vision_time_s
            self._rgb=rgb; self._luminance=luminance
        return SensoryFrame(time_s,vision_time_s,fresh,rgb,luminance,contrast,angles,velocity,
                            _snapshot(np.linalg.norm(forces,axis=1)),motor)


def from_flygym(stream, *, time_s, vision_time_s, observation, raw_vision, previous_motor_command):
    """Whitelist peripheral measurements; ignore global position and evaluator data.

Caller supplies the actual image acquisition time, not merely the polling time.
Contact load is a mechanical proxy; no anatomical transduction is asserted.
"""
    joints=np.asarray(observation['joints'])
    if joints.ndim!=2 or joints.shape[0]<2: raise ValueError('Bad FlyGym joints')
    return stream.update(time_s=time_s,vision_time_s=vision_time_s,eye_rgb=raw_vision,
                         joint_angles_rad=joints[0],joint_velocities_rad_s=joints[1],
                         contact_forces=observation['contact_forces'],
                         previous_motor_command=previous_motor_command)


def rest_capable_drive(activity=0., turn=0.):
    """Motor capability only. Choosing activity needs a separately validated circuit."""
    if not np.isfinite([activity,turn]).all() or not 0<=activity<=1 or not -1<=turn<=1:
        raise ValueError('Activity must be 0..1 and turn -1..1')
    return activity*np.array([1+.3*turn,1-.3*turn])
