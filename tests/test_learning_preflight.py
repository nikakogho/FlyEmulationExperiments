import unittest
import numpy as np
from flyplasticity.learning_preflight import NeuralPreflightGuard


class LearningPreflightTests(unittest.TestCase):
    def test_measured_ppl1_activity_latches_stop(self):
        guard=NeuralPreflightGuard(3,[2]);z=np.zeros(3)
        guard.inspect(0,z,z,z,z,z)
        with self.assertRaises(RuntimeError):guard.inspect(.005,[0,0,1],z,z,z,z)
        self.assertTrue(guard.guard.stopped)
        with self.assertRaises(RuntimeError):guard.inspect(.01,z,z,z,z,z)

    def test_missing_telemetry_or_unexpected_reward_rejected(self):
        for counts,reward in [([0,0],np.zeros(3)),(np.zeros(3),[0,1,0]),([0,np.nan,0],np.zeros(3))]:
            guard=NeuralPreflightGuard(3,[2]);z=np.zeros(3)
            with self.assertRaises(RuntimeError):guard.inspect(0,counts,z,z,z,reward)

    def test_recovery_quiet_and_clock(self):
        guard=NeuralPreflightGuard(3,[2]);z=np.zeros(3)
        row=guard.inspect(0,z,z,z,z,z);self.assertEqual(row['total_spikes'],0)
        with self.assertRaises(RuntimeError):guard.inspect(.1,z,z,z,z,z)


if __name__=='__main__':unittest.main()
