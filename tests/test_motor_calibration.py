import unittest
import numpy as np
from flyplasticity.motor_calibration import (
    hyperpolarizing_voltage_prediction, probe_force_un, require_exact_identity)


class MotorCalibrationTests(unittest.TestCase):
    def test_resistance_units_and_no_spike_regime_extrapolation(self):
        np.testing.assert_allclose(hyperpolarizing_voltage_prediction([-5, 0]), [-61.5, -60])
        for bad in (1, -6, float('nan'), float('inf')):
            with self.assertRaises(ValueError): hyperpolarizing_voltage_prediction(bad)

    def test_probe_static_units_and_signed_dynamics(self):
        self.assertAlmostEqual(float(probe_force_un(50, 0, 0)), 11.17)
        self.assertAlmostEqual(float(probe_force_un(5, 0, 0)), 1.117)
        self.assertAlmostEqual(float(probe_force_un(0, 1000, 0)), .14)
        self.assertAlmostEqual(float(probe_force_un(0, 0, 1e6)), .17)
        self.assertAlmostEqual(float(probe_force_un(-50, -1000, -1e6)), -11.48)

    def test_bad_trace_arrays_rejected(self):
        for args in (([1,2], [0], [0]), ([1,float('nan')], [0,0], [0,0])):
            with self.assertRaises(ValueError): probe_force_un(*args)

    def test_rank_and_candidate_cannot_be_used_as_identity(self):
        for status in ('candidate', 'unresolved', None):
            with self.assertRaises(ValueError):
                require_exact_identity(dict(status=status, root_id='648518346496932836', rank='3'))
        with self.assertRaises(ValueError):
            require_exact_identity(dict(status='confirmed_exact_crosswalk',
                                        root_id='648518346484809885', driver='R22A08-Gal4',
                                        crosswalk_source='synthetic fixture'))


if __name__ == '__main__': unittest.main()
