import unittest
import numpy as np
from flyplasticity.odor_scene import OdorField,OrnTransport

class OdorSceneTests(unittest.TestCase):
    def test_three_dimensional_distance_rotation_and_translation(self):
        sources=np.array([[1.,2.,3.],[5.,2.,1.]])
        sensors=np.array([[1.,2.,3.],[1.,2.,9.]])
        field=OdorField(sources);sample=field.sample(sensors)
        self.assertEqual(sample[0,0],1);self.assertLess(sample[0,1],1)
        rot=np.array([[0,-1,0],[1,0,0],[0,0,1]])
        np.testing.assert_allclose(sample,OdorField(sources@rot+7).sample(sensors@rot+7))

    def test_source_swap_does_not_relabel_cues(self):
        s=np.array([[0.,1,0],[0,-1,0]]);p=np.array([[0,1,0],[0,-1,0]])
        np.testing.assert_allclose(OdorField(s[::-1]).sample(p),OdorField(s).sample(p)[::-1])

    def test_antenna_and_palp_are_not_confused(self):
        c=np.array([[.1,.2,.3,.4],[.5,.6,.7,.8]])
        t=OrnTransport([0,0,1,1],['left','right','left','right'],['AN','AN','MxLbN','MxLbN'])
        np.testing.assert_allclose(t.rates(c,0,0),[150,200,250,300])

    def test_unknown_side_is_explicitly_symmetric(self):
        t=OrnTransport([0],['na'],['AN']);self.assertEqual(t.unknown_sides,1)
        self.assertEqual(t.rates([[0,0,.2,.8],[0,0,0,0]],0,0)[0],250)

    def test_bad_data_or_stale_samples_rejected(self):
        for c,s,n in [(np.zeros((2,3)),0,0),(np.full((2,4),np.nan),0,0),
                      (np.zeros((2,4)),0,.006),(np.zeros((2,4)),.01,0)]:
            with self.assertRaises(ValueError):OrnTransport([0],['left'],['AN']).rates(c,s,n)
        t=OrnTransport([0],['left'],['AN']);t.rates(np.zeros((2,4)),0,0)
        with self.assertRaises(ValueError):t.rates(np.zeros((2,4)),0,0)

if __name__=='__main__':unittest.main()
