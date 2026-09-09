"""Offline trace analysis only: no neurons, force commands or simulation steps.

The pre-displacement angle is an evaluation reference, never a controller input.
Passing these numerical checks does not establish biological fidelity or welfare.
"""
from dataclasses import dataclass
import numpy as np


def vector(values, name):
    x = np.asarray(values, dtype=float)
    if x.ndim != 1 or len(x) < 3 or not np.isfinite(x).all():
        raise ValueError(f'{name}: need at least three finite samples')
    return x


@dataclass(frozen=True)
class Trace:
    time_s: object
    angle_deg: object
    external_torque: object
    motor_output: object

    def arrays(self):
        arrays = [vector(getattr(self, k), k) for k in self.__dataclass_fields__]
        if len({len(a) for a in arrays}) != 1:
            raise ValueError('Trace lengths differ')
        if arrays[0][0] != 0 or np.any(np.diff(arrays[0]) <= 0):
            raise ValueError('Time must start at zero and increase')
        return arrays


def compare_reflex(intact, sensory_cut, motor_cut, *, reference_deg,
                   minimum_effect_deg, matching_atol=1e-9):
    """Compare matched release trials, using absolute-error area after release.

    Caller must supply the same starting displaced state, release time grid and
    external forces. Entire traces are post-release; pre-release data do not enter
    this metric. A motor-cut trace must contain zero delivered motor output.
    Causal interpretation additionally requires independently audited ablations.
    """
    if not np.isfinite(reference_deg) or not np.isfinite(minimum_effect_deg) or minimum_effect_deg <= 0:
        raise ValueError('Specify finite reference and positive effect threshold')
    if not np.isfinite(matching_atol) or matching_atol < 0:
        raise ValueError('Bad matching tolerance')
    trials = [t.arrays() for t in (intact, sensory_cut, motor_cut)]
    time, angle, force, _ = trials[0]
    for t, a, f, _ in trials[1:]:
        if (t.shape != time.shape or not np.array_equal(t, time)
                or not np.allclose(f, force, rtol=0, atol=matching_atol)
                or abs(a[0]-angle[0]) > matching_atol):
            raise ValueError('Unmatched time, perturbation force or starting angle')
    if np.any(np.abs(trials[2][3]) > matching_atol):
        raise ValueError('Motor-cut trial still delivers motor output')
    initial_error = abs(angle[0]-reference_deg)
    if initial_error <= minimum_effect_deg:
        raise ValueError('Displacement must exceed effect threshold')
    def metric(a):
        error = np.abs(a-reference_deg)
        # Trapezoidal mean absolute error: penalizes overshoot and ignores sign.
        mae = float(np.sum((error[1:]+error[:-1])*.5*np.diff(time))/time[-1])
        return dict(mean_error_deg=mae, final_error_deg=float(error[-1]))
    metrics = dict(zip(('intact', 'sensory_cut', 'motor_cut'), [metric(v[1]) for v in trials]))
    benefit = {key: metrics[key]['mean_error_deg']-metrics['intact']['mean_error_deg']
               for key in ('sensory_cut', 'motor_cut')}
    passed = (initial_error-metrics['intact']['final_error_deg'] >= minimum_effect_deg
              and min(benefit.values()) >= minimum_effect_deg)
    return dict(numerical_criterion_passed=bool(passed), metrics=metrics,
                improvement_over_cuts_deg=benefit,
                biological_validation=False, welfare_assessment='not_assessed_by_trace_metric')


def subthreshold_response(voltage_mv, spike_count, *, baseline_mv, threshold_mv):
    """Check an offline weak-input response without turning an EPSP into force.

    Voltage and threshold must share a measurement compartment. This is a
    protocol-specific expectation, not a rule that all fly reflexes lack spikes.
    """
    v = vector(voltage_mv, 'voltage_mv')
    if not np.isfinite([baseline_mv, threshold_mv]).all() or threshold_mv <= baseline_mv:
        raise ValueError('Invalid baseline/threshold')
    if type(spike_count) is not int or spike_count < 0:
        raise ValueError('Invalid spike count')
    return dict(depolarized=bool(v.max() > baseline_mv),
                stayed_subthreshold=bool(v.max() < threshold_mv),
                no_spikes=spike_count == 0,
                compatible=bool(baseline_mv < v.max() < threshold_mv and spike_count == 0))


def heldout_error(observed, predicted, baseline_prediction):
    """Data-fit score; use independent animals/trials, not randomly split frames.

    Units are inherited from the input (e.g. calcium remains calcium, not Hz).
    This function cannot establish split provenance; record it alongside scores.
    """
    y, p, b = [vector(x, 'response') for x in (observed, predicted, baseline_prediction)]
    if y.shape != p.shape or y.shape != b.shape:
        raise ValueError('Response lengths differ')
    mse, baseline_mse = float(np.mean((y-p)**2)), float(np.mean((y-b)**2))
    return dict(rmse=mse**.5, baseline_rmse=baseline_mse**.5,
                beats_baseline=mse < baseline_mse,
                skill_vs_baseline=None if baseline_mse == 0 else 1-mse/baseline_mse)
