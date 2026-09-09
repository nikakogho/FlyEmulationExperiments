"""Actuator interface and transition checks, without a neural simulation."""
import unittest
from types import SimpleNamespace
from unittest.mock import patch
import numpy as np
from flygym import SingleFlySimulation
from flygym.examples.locomotion import HybridTurningController, PreprogrammedSteps
from flyplasticity.standing import StandingController


class StandingTests(unittest.TestCase):
    def controller(self):
        obj = StandingController.__new__(StandingController)
        obj.curr_time = 0.
        obj._standing_start = None
        obj._standing_angles = None
        obj.preprogrammed_steps = PreprogrammedSteps()
        obj.get_observation = lambda: {'joints': np.zeros((3, 42))}
        return obj

    def test_stance_uses_42_actuators_and_advances_physics(self):
        obj = self.controller()
        result = ({}, 0, False, False, {})
        with patch.object(SingleFlySimulation, 'step', return_value=result) as step:
            obj.step([0, 0])
            first = step.call_args.args[1]
            self.assertEqual(first['joints'].shape, (42,))
            np.testing.assert_array_equal(first['joints'], 0)
            np.testing.assert_array_equal(first['adhesion'], 1)
            obj.curr_time = .05
            obj.step([0, 0])
            np.testing.assert_allclose(step.call_args.args[1]['joints'],
                                       .5*obj.preprogrammed_steps.default_pose)
            obj.curr_time = .2
            obj.step([0, 0])
            np.testing.assert_array_equal(step.call_args.args[1]['joints'],
                                          obj.preprogrammed_steps.default_pose)
            self.assertEqual(step.call_count, 3)

    def test_resume_clears_old_corrections(self):
        obj = self.controller()
        obj._standing_start = 0.
        obj.cpg_network = SimpleNamespace(curr_magnitudes=np.ones(6))
        obj.retraction_correction = np.ones(6)
        obj.stumbling_correction = np.ones(6)
        obj.retraction_persistence_counter = np.ones(6)
        with patch.object(HybridTurningController, 'step', return_value='walking'):
            self.assertEqual(obj.step([.6, .6]), 'walking')
        self.assertIsNone(obj._standing_start)
        np.testing.assert_array_equal(obj.cpg_network.curr_magnitudes, 0)
        np.testing.assert_array_equal(obj.retraction_persistence_counter, 0)
        np.testing.assert_array_equal(obj.retraction_correction, 0)
        np.testing.assert_array_equal(obj.stumbling_correction, 0)

    def test_invalid_commands(self):
        obj = self.controller()
        for command in ([0], [0, 0, 0], [np.nan, 0], [np.inf, 0]):
            with self.assertRaises(ValueError):
                obj.step(command)


if __name__ == '__main__':
    unittest.main()
