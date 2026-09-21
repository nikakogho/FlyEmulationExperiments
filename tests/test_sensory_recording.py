import unittest
from dataclasses import fields
import numpy as np
from flyplasticity.sensory_recording import SpectralBodyStream, SpectralBodyFrame, project_world, scheduled_command


class SensoryRecordingTests(unittest.TestCase):
    def values(self, t=0):
        return dict(time_s=t, acquisition_s=[t]*4, eye_excitation=np.ones((2, 3, 3)),
            joint_angles_rad=[0, 1], joint_velocities_rad_s=[1, 0],
            contact_vectors_native=[[0, 0, 1]], odor_concentration=[[.1, .2, .3, .4]],
            previous_command=[0, 0])

    def test_snapshot_and_whitelist(self):
        values = self.values()
        packet = SpectralBodyStream().update(**values)
        values['eye_excitation'][:] = 0
        self.assertTrue(np.all(packet.eye_excitation == 1))
        with self.assertRaises(ValueError):
            packet.eye_excitation[0, 0, 0] = 2
        self.assertFalse({'position', 'heading', 'reward', 'source', 'target'} & {f.name for f in fields(SpectralBodyFrame)})
        self.assertIn('neural_proprioception', packet.unavailable)

    def test_timing_failure_does_not_commit(self):
        stream = SpectralBodyStream()
        stream.update(**self.values())
        for t in (0, -.01, .02):
            with self.assertRaises(ValueError): stream.update(**self.values(t))
        bad = self.values(.01); bad['acquisition_s'][0] = 0
        with self.assertRaises(ValueError): stream.update(**bad)
        stream.update(**self.values(.01))

    def test_shape_range_nan_rejected(self):
        for key, value in [('odor_concentration', [[-1]*4]), ('eye_excitation', np.zeros((2, 3))),
            ('joint_velocities_rad_s', [0]), ('contact_vectors_native', [[np.nan, 0, 0]]),
            ('previous_command', [2, 0]), ('acquisition_s', [0]*3)]:
            bad = self.values(); bad[key] = value
            with self.assertRaises(ValueError): SpectralBodyStream().update(**bad)

    def test_layout_change_rejected(self):
        s = SpectralBodyStream(); s.update(**self.values())
        bad = self.values(.01); bad['eye_excitation'] = np.ones((2, 4, 3))
        with self.assertRaises(ValueError): s.update(**bad)

    def test_camera_handedness_and_depth(self):
        def project(p): return project_world(p, [0, 0, 0], np.eye(3), 90, (100, 100))
        np.testing.assert_allclose(project([0, 0, -2]), [49.5, 49.5])
        np.testing.assert_allclose(project([1, 1, -2]), [24.5, 74.5])
        np.testing.assert_allclose(project([2, 2, -4]), project([1, 1, -2]))
        with self.assertRaises(ValueError): project([0, 0, 1])

    def test_rigid_rotation_preserves_retinal_point(self):
        r = np.array([[0, -1, 0], [1, 0, 0], [0, 0, 1]])
        p = np.array([1., 0, -3]); c = np.array([4., 5, 6])
        np.testing.assert_allclose(project_world(r@p+c, c, r, 90, (100, 100)),
                                   project_world(p, np.zeros(3), np.eye(3), 90, (100, 100)))

    def test_fixed_schedule_includes_rest_and_turn(self):
        for t in (0, .2, 2.1, 3.): np.testing.assert_array_equal(scheduled_command(t), 0)
        self.assertNotEqual(*scheduled_command(1.3))
        np.testing.assert_array_equal(scheduled_command(.5), [.6, .6])


if __name__ == '__main__': unittest.main()
