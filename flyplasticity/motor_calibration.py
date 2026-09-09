"""Offline physiological calibration utilities. No neuronal state or actuation.

Reference values are published, rounded class summaries, not parameters fitted
to the selected FANC cell. Somatic input resistance is not a spike threshold.
"""
import numpy as np

INTERMEDIATE_REFERENCE = {
    'driver': 'R22A08-Gal4',
    'resting_soma_voltage_mv': -60.0,
    'input_resistance_mohm': 300.0,
    'resting_spike_rate_hz': 0.0,
    'parameter_kind': 'rounded_published_class_summary_not_cell_fit',
    'spike_threshold_mv': None,
    'source': 'https://elifesciences.org/articles/56754',
}


def hyperpolarizing_voltage_prediction(current_pa):
    """Local Ohmic prediction over -5..0 pA from the reported resistance assay.

    No extrapolation to depolarizing currents, spikes, or sensory synapses.
    This calculation is a reference prediction, not an independently fitted curve.
    """
    i = np.asarray(current_pa, dtype=float)
    if not np.isfinite(i).all() or np.any((i < -5) | (i > 0)):
        raise ValueError('Only the small hyperpolarizing reference regime is supported')
    return -60.0 + i * 300.0 * 1e-3  # pA * Mohm -> mV


def probe_force_un(displacement_um, velocity_um_s, acceleration_um_s2):
    """Force on the calibrated experimental probe, in the deflection direction.

    F = k*x + c*v + m*a. These are PROBE properties in saline, not muscle or
    fly-leg properties. Derivatives must be supplied by a validated trace-analysis
    procedure; differentiating noisy pixels naively is not endorsed here.
    Azevedo Fig 1 supplement 2: k=.2234 N/m, c=.14e-3 kg/s, m=.17 mg.
    """
    arrays = [np.asarray(v, dtype=float) for v in
              (displacement_um, velocity_um_s, acceleration_um_s2)]
    if len({a.shape for a in arrays}) != 1 or not all(np.isfinite(a).all() for a in arrays):
        raise ValueError('Require matching finite displacement and derivative arrays')
    x, v, a = arrays
    # micrometres -> metres and newtons -> micronewtons cancel.
    return .2234 * x + .14e-3 * v + .17e-6 * a


def require_exact_identity(evidence):
    """Reject assigning class parameters to an unconfirmed anatomical candidate."""
    if evidence.get('status') != 'confirmed_exact_crosswalk':
        raise ValueError('Physiological identity is a candidate, not a confirmed crosswalk')
    if (evidence.get('root_id') != '648518346496932836'
            or evidence.get('driver') != 'R22A08-Gal4'
            or not evidence.get('crosswalk_source')):
        raise ValueError('Missing or mismatched exact identity evidence')
    return dict(INTERMEDIATE_REFERENCE)
