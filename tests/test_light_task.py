import inspect
import unittest
import numpy as np
from flyplasticity.light_task import visual_features,motor_output,LocalEligibilityLTD


class LightBoundaryTests(unittest.TestCase):
    def test_pixels_only_and_neutral_background(self):
        self.assertEqual(list(inspect.signature(visual_features).parameters),['eye_images'])
        np.testing.assert_array_equal(visual_features(np.full((2,4,4,3),120)),np.zeros((2,2)))

    def test_color_and_eye_swap(self):
        image=np.zeros((2,10,10,3),dtype=np.uint8)
        image[0,:2,:2,1]=255; image[1,:2,:2,2]=255
        features=visual_features(image)
        self.assertGreater(features[0,0],0); self.assertGreater(features[1,1],0)
        self.assertEqual(features[0,1],0); self.assertEqual(features[1,0],0)
        np.testing.assert_array_equal(visual_features(image[::-1]),features[::-1])
        np.testing.assert_array_equal(visual_features(image[:,:,:,[0,2,1]]),features[:,::-1])

    def test_controller_cannot_receive_goal_or_reward(self):
        self.assertEqual(list(inspect.signature(motor_output).parameters),['mbon_rates','exploration'])
        np.testing.assert_array_equal(motor_output([20,20],0),[1,1])
        np.testing.assert_array_equal(motor_output([10,40],0),motor_output([40,10],0)[::-1])
        self.assertTrue(np.all(motor_output([0,1000],1)<=1.3))

    def test_rule_sees_counts_and_weights_only(self):
        self.assertEqual(list(inspect.signature(LocalEligibilityLTD.step).parameters),['self','counts','weights'])

    def test_no_dopamine_no_update(self):
        r=LocalEligibilityLTD([0,1],[2],3)
        w=np.array([1.,2.])
        for _ in range(100): w=r.step([1,0,0],w)
        np.testing.assert_array_equal(w,[1,2])

    def test_reward_changes_active_connection_preserves_sign(self):
        r=LocalEligibilityLTD([0,1],[2],3)
        w=np.array([1.,2.]); new=r.step([1,0,2],w)
        self.assertTrue(0<new[0]<1); self.assertEqual(new[1],2)
        np.testing.assert_array_equal(w,[1,2])

    def test_temporal_decay_reduces_delayed_association(self):
        changes=[]
        for gap in (0,100):
            r=LocalEligibilityLTD([0],[1],2); w=np.array([1.])
            r.step([1,0],w)
            for _ in range(gap): r.step([0,0],w)
            changes.append(1-r.step([0,2],w)[0])
        self.assertGreater(changes[0],changes[1]*1000)


if __name__=='__main__': unittest.main()
