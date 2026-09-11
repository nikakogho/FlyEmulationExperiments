import unittest
from scripts.audit_saved_motor_readout import decode
from flyplasticity.neural_speed import NeuralSpeed


class SavedMotorTests(unittest.TestCase):
    def test_sum_representation_exactly_matches_split_counts(self):
        rows=[dict(time_s=k*.005,observed_phase='probe',mbon01_spikes=3) for k in range(80)]
        decoded=decode(rows);motor=NeuralSpeed()
        for r in decoded:self.assertEqual(r['command'],motor.step([1,2]).tolist())

    def test_missing_bin_rejected(self):
        with self.assertRaises(ValueError):decode([dict(time_s=.005,observed_phase='probe',mbon01_spikes=0)])

    def test_invalid_counts_rejected(self):
        with self.assertRaises(ValueError):decode([dict(time_s=0,observed_phase='probe',mbon01_spikes=-1)])
