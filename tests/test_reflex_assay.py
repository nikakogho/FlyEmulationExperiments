import unittest
import numpy as np
from flyplasticity.reflex_assay import Trace, compare_reflex, subthreshold_response, heldout_error


class ReflexAssayTests(unittest.TestCase):
    def trace(self, angles, output=0):
        n = len(angles)
        return Trace(np.linspace(0, 1, n), angles, np.zeros(n), np.full(n, output))

    def compare(self, intact, sensory=None, motor=None):
        return compare_reflex(self.trace(intact, 1), self.trace(sensory or [101]*5),
                              self.trace(motor or [101]*5), reference_deg=100, minimum_effect_deg=.1)

    def test_correction_requires_both_ablations(self):
        trajectory = [101, 100.7, 100.4, 100.1, 100]
        self.assertTrue(self.compare(trajectory)['numerical_criterion_passed'])
        self.assertFalse(self.compare(trajectory, sensory=trajectory)['numerical_criterion_passed'])
        self.assertFalse(self.compare(trajectory, motor=trajectory)['numerical_criterion_passed'])

    def test_passive_return_cannot_count_as_reflex(self):
        a = [101, 100.7, 100.4, 100.1, 100]
        self.assertFalse(self.compare(a, a, a)['numerical_criterion_passed'])

    def test_wrong_direction_and_overshoot_fail(self):
        for a in ([101, 101.2, 101.5, 101.8, 102], [101, 95, 95, 95, 100]):
            self.assertFalse(self.compare(a)['numerical_criterion_passed'])

    def test_mismatched_or_nonfinite_trials_rejected(self):
        base = self.trace([101]*5)
        variants = [self.trace([102]*5), self.trace([101]*4),
                    Trace([0,.2,.2,.6,1], [101]*5, [0]*5, [0]*5),
                    Trace([0,.25,.5,.75,1], [101]*5, [1]*5, [0]*5),
                    self.trace([101,101,float('nan'),101,101])]
        for v in variants:
            with self.assertRaises(ValueError):
                compare_reflex(base, v, base, reference_deg=100, minimum_effect_deg=.1)
        with self.assertRaises(ValueError):
            compare_reflex(base, base, self.trace([101]*5, 1), reference_deg=100, minimum_effect_deg=.1)

    def test_epsp_does_not_imply_spike(self):
        # Synthetic numerical fixture, not a fitted cell or biological threshold.
        r = subthreshold_response([-60,-57,-59], 0, baseline_mv=-60, threshold_mv=-45)
        self.assertTrue(r['compatible'])
        self.assertFalse(subthreshold_response([-60,-57,-59], 1, baseline_mv=-60, threshold_mv=-45)['compatible'])
        self.assertFalse(subthreshold_response([-60,-44,-59], 0, baseline_mv=-60, threshold_mv=-45)['compatible'])

    def test_fit_must_beat_baseline_and_zero_variance_is_defined(self):
        self.assertFalse(heldout_error([0,1,2], [0,0,0], [1,1,1])['beats_baseline'])
        r = heldout_error([0,1,2], [0,1,2], [1,1,1])
        self.assertEqual(r['skill_vs_baseline'], 1)
        self.assertIsNone(heldout_error([1]*3, [1]*3, [1]*3)['skill_vs_baseline'])


if __name__ == '__main__': unittest.main()
