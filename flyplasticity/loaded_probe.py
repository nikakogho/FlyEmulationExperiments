"""Measured probe mechanics, SI-derived units; no neural simulation."""
import numpy as np
from scipy.signal import cont2discrete, lfilter
from scipy.optimize import least_squares
from .figure_twitch import twitch

MASS_KG = .17e-6
DAMPING_KG_S = .14e-3
STIFFNESS_N_M = .2234


def response(time_ms, force_parameters, dt_s=.00002):
    """uN force -> um displacement; factors of 1e-6 cancel in the ODE.

    Force waveform is a descriptive fit, not a recovered muscle mechanism.
    """
    t = np.asarray(time_ms, dtype=float)
    if t.ndim != 1 or not len(t) or not np.isfinite(t).all() or np.max(t) > 1000 or not np.isfinite(dt_s) or not 0<dt_s<=.001:
        raise ValueError('Invalid probe evaluation window')
    grid = np.arange(0, max(0., t.max()/1000)+2*dt_s, dt_s)
    b, a, _ = cont2discrete(([1], [MASS_KG, DAMPING_KG_S, STIFFNESS_N_M]), dt_s)
    force = twitch(grid*1000, *force_parameters)
    x = lfilter(b.ravel(), a, force)
    return np.where(t < 0, 0, np.interp(t/1000, grid, x))


def fit_force(traces):
    def residual(z):
        return np.concatenate([(response(t, z)-y)/np.sqrt(len(t)) for t, y in traces])
    fit = least_squares(residual, [.9, 5, 2], bounds=([0, 1, 0], [10, 40, 10]))
    if not fit.success: raise ValueError('Mechanical fit failed')
    return fit.x.tolist()


def mujoco_probe(dt=.00002):
    """Native mm/mg/s model with exact conversion of published SI probe load."""
    import mujoco
    xml = f'''<mujoco model="calibrated_probe"><option timestep="{dt}" gravity="0 0 0" integrator="implicitfast"/>
    <worldbody><light pos="0 0 2"/><body name="probe"><inertial pos="0 0 0" mass="{MASS_KG*1e6}" diaginertia=".001 .001 .001"/>
    <joint name="deflection" type="slide" axis="1 0 0" stiffness="{STIFFNESS_N_M*1e6}" damping="{DAMPING_KG_S*1e6}"/>
    <geom type="capsule" fromto="0 -.08 0 0 .08 0" size=".002" rgba=".2 .7 .8 1" contype="0" conaffinity="0"/>
    </body></worldbody><actuator><motor joint="deflection" gear="1"/></actuator></mujoco>'''
    model = mujoco.MjModel.from_xml_string(xml)
    return model, mujoco.MjData(model), xml
