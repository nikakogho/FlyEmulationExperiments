import unittest
import numpy as np
from flyplasticity.figure_twitch import twitch,fit_twitch
from scripts.match_motor_atlas import mesh_xy,image_distance


class MotorEvidenceTests(unittest.TestCase):
    def test_causal_pulse_and_recovery(self):
        t=np.linspace(0,120,80);y=twitch(t,4.5,8,6)
        self.assertTrue(np.all(y[t<=6]==0))
        fit=fit_twitch(t,y)
        self.assertAlmostEqual(fit['amplitude_um'],4.5,places=5)
        self.assertAlmostEqual(fit['time_to_peak_ms'],22,places=5)
        with self.assertRaises(ValueError):twitch(t,1,0,0)
        with self.assertRaises(ValueError):fit_twitch([0,1,1]*3,[0]*9)
        with self.assertRaises(ValueError):fit_twitch(t,np.full_like(t,np.nan))

    def test_mesh_units_and_malformed_input(self):
        vertices=np.array([[1000,2000,3000],[4000,6000,8000]],dtype='<f4')
        raw=np.array([2],dtype='<u4').tobytes()+vertices.tobytes()
        np.testing.assert_array_equal(mesh_xy(raw),[[0,0],[3,4]])
        with self.assertRaises(ValueError):mesh_xy(raw[:10])

    def test_out_of_frame_cannot_improve_match(self):
        p=np.array([[1,1],[2,2]])
        self.assertEqual(image_distance(p,np.array([1,0,0]),np.zeros((10,10))),0)
        self.assertEqual(image_distance(p,np.array([1,100,100]),np.zeros((10,10))),30)


if __name__=='__main__':unittest.main()
