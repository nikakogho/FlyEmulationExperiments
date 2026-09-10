import unittest,inspect
import numpy as np
from flyplasticity.neural_speed import NeuralSpeed

class NeuralSpeedTests(unittest.TestCase):
    def test_neural_only_interface_and_no_direction(self):
        m=NeuralSpeed();self.assertEqual(list(inspect.signature(m.step).parameters),['output_spikes'])
        for k in range(100):
            u=m.step([1,0]);self.assertEqual(u[0],u[1]);self.assertTrue(np.all((u>=.35)&(u<=.7)))
    def test_lower_activity_reduces_command(self):
        low=NeuralSpeed();high=NeuralSpeed()
        for k in range(100):a=low.step([0,0]);b=high.step([1,1])
        self.assertLess(a[0],b[0])
    def test_invalid_counts_rejected(self):
        for x in ([1],[-1,0],[np.nan,0],[.2,0]):
            with self.assertRaises(ValueError):NeuralSpeed().step(x)

if __name__=='__main__':unittest.main()
