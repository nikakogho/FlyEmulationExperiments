import unittest
import numpy as np
from flyplasticity.joint_rig import JointRig


class JointTests(unittest.TestCase):
    def test_antagonism_rest_and_force(self):
        results = []
        for cmd in ([1,0],[0,1],[1,1],[0,0]):
            rig = JointRig()
            for _ in range(500):
                rig.step(cmd)
            results.append(rig.observe()['angle_rad'])
            self.assertLessEqual(abs(rig.observe()['torque_nm']), .002001)
            self.assertLess(abs(results[-1]), 1.)
        self.assertGreater(results[0],.1)
        self.assertAlmostEqual(results[0],-results[1],places=12)
        self.assertAlmostEqual(results[2],0.)
        self.assertAlmostEqual(results[3],0.)

    def test_passive_return(self):
        rig = JointRig()
        for _ in range(500): rig.step([1,0])
        initial = abs(rig.data.qpos[0])
        for _ in range(2500): rig.step([0,0])
        self.assertLess(abs(rig.data.qpos[0]), initial*.01)

    def test_fault_freezes_physics_and_latches(self):
        rig = JointRig()
        rig.step([1,0])
        before = rig.data.qpos.copy(), rig.data.time, rig.steps
        for fault in [True,False]:
            with self.assertRaises(RuntimeError): rig.step([1,0],fault=fault)
            np.testing.assert_array_equal(before[0],rig.data.qpos)
            self.assertEqual(before[1:],(rig.data.time,rig.steps))

    def test_no_neural_attachment_or_invalid_commands(self):
        with self.assertRaises(ValueError): JointRig(neural_model=object())
        rig = JointRig()
        with self.assertRaises(ValueError): rig.step([float('nan'),0])
        with self.assertRaises(RuntimeError): rig.step([0,0])
        self.assertEqual(rig.steps,0)

    def test_observations_do_not_change_dynamics(self):
        a,b=JointRig(),JointRig()
        for _ in range(100):
            a.observe(); a.observe()
            a.step([.5,0]); b.step([.5,0])
        np.testing.assert_array_equal(a.data.qpos,b.data.qpos)
        self.assertAlmostEqual(a.data.time,.1)
