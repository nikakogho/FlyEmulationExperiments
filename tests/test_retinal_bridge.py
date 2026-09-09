import unittest
import numpy as np
from flyplasticity.retinal_bridge import RetinalBridge,sample_hold

class RetinalTests(unittest.TestCase):
    def test_sample_hold_no_future_information(self):
        v,t=sample_hold(np.array([1,9,3]),[0,.02,.04],[0,.005,.019,.02,.035,.04])
        np.testing.assert_array_equal(v,[1,1,1,9,9,3])
        np.testing.assert_allclose(t,[0,0,0,.02,.02,.04])
        for q in ([-.001],[.08]):
            with self.assertRaises(ValueError):sample_hold([1,2],[0,.02],q)

    def test_permutation_and_background_exclusion(self):
        ids=np.array([[1,1,0,2,2],[3,3,0,4,4]])
        target=np.array([[1,1],[0,0],[1,0],[0,1]])
        b=RetinalBridge(ids,target)
        img=np.zeros((2,2,5,3));img[:,:,2]=255
        np.testing.assert_array_equal(b.encode(img),0)
        with self.assertRaises(ValueError):b.encode(np.full_like(img,np.nan))

    def test_non_bijective_geometry_rejected(self):
        with self.assertRaises(ValueError):RetinalBridge(np.array([[1,2],[3,4]]),np.zeros((4,2)))

    def test_color_transport_preserves_cues_that_grayscale_aliases(self):
        b=RetinalBridge(np.array([[1,2],[3,4]]),np.array([[0,0],[0,1],[1,0],[1,1]]))
        green=np.broadcast_to([13,255,13],(2,2,2,3))
        blue=green[...,[0,2,1]]
        np.testing.assert_array_equal(b.encode(green),b.encode(blue))
        self.assertGreater(np.max(np.abs(b.encode_rgb(green)-b.encode_rgb(blue))),.9)
        np.testing.assert_allclose(b.encode_rgb(green)[0,0],[13/255,1,13/255])

if __name__=='__main__':unittest.main()
