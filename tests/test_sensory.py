import unittest
import numpy as np
from flyplasticity.sensory import SensoryStream,from_flygym,rest_capable_drive


def sample(t=0.,image=None,**overrides):
    result=dict(time_s=t,vision_time_s=t,eye_rgb=np.zeros((2,8,8,3)) if image is None else image,
                joint_angles_rad=np.array([.1,.2]),joint_velocities_rad_s=np.array([.3,.4]),
                contact_forces=np.array([[3.,4.,0.],[0.,0.,0.]]),previous_motor_command=np.zeros(2))
    result.update(overrides); return result


class SensoryTests(unittest.TestCase):
    def test_spatial_information_survives_equal_global_means(self):
        a=np.zeros((2,8,8,3)); a[:,2,2]=100
        b=np.roll(a,2,axis=2)
        stream=SensoryStream(); x=stream.update(**sample(image=a)); y=stream.update(**sample(.02,b))
        self.assertEqual(x.luminance.mean(),y.luminance.mean())
        self.assertFalse(np.array_equal(x.luminance,y.luminance))
        self.assertTrue(np.any(y.temporal_contrast_per_s>0)); self.assertTrue(np.any(y.temporal_contrast_per_s<0))

    def test_stationary_scene_has_zero_temporal_change(self):
        s=SensoryStream(); s.update(**sample()); f=s.update(**sample(.02))
        np.testing.assert_array_equal(f.temporal_contrast_per_s,0)

    def test_temporal_derivative_uses_acquisition_interval(self):
        image=np.full((2,8,8,3),51.)
        s=SensoryStream(); s.update(**sample()); f=s.update(**sample(.025,image,vision_time_s=.02))
        np.testing.assert_allclose(f.temporal_contrast_per_s,10.)

    def test_stale_sample_is_not_fake_motion_measurement(self):
        s=SensoryStream(); s.update(**sample()); f=s.update(**sample(.01,vision_time_s=0))
        self.assertFalse(f.vision_fresh); self.assertIsNone(f.temporal_contrast_per_s)

    def test_inconsistent_duplicate_rejected(self):
        s=SensoryStream(); s.update(**sample())
        with self.assertRaises(ValueError): s.update(**sample(.01,np.ones((2,8,8,3)),vision_time_s=0))
        # Rejected input must not advance the stream.
        s.update(**sample(.01,vision_time_s=0))

    def test_timestamp_contract(self):
        for change in ({'time_s':0}, {'time_s':.1,'vision_time_s':.1},
                       {'time_s':.02,'vision_time_s':.03},{'time_s':.04,'vision_time_s':0}):
            s=SensoryStream(); s.update(**sample())
            with self.assertRaises(ValueError): s.update(**sample(**change))

    def test_reset_has_no_cross_episode_motion(self):
        s=SensoryStream(); s.update(**sample()); s.reset()
        f=s.update(**sample(image=np.full((2,8,8,3),255)))
        self.assertIsNone(f.temporal_contrast_per_s)

    def test_no_aliasing_and_contact_magnitude(self):
        a=sample(); f=SensoryStream().update(**a); a['joint_angles_rad'][:]=999
        np.testing.assert_array_equal(f.joint_angles_rad,[.1,.2])
        np.testing.assert_array_equal(f.contact_load_native_units,[5,0])
        with self.assertRaises(ValueError): f.rgb[:]=1

    def test_body_and_retina_are_separate_channels(self):
        s=SensoryStream(); a=s.update(**sample())
        b=s.update(**sample(.02,joint_angles_rad=np.array([1.,2.])))
        np.testing.assert_array_equal(a.rgb,b.rgb)
        self.assertFalse(np.array_equal(a.joint_angles_rad,b.joint_angles_rad))

    def test_global_coordinates_and_rewards_cannot_change_packet(self):
        obs=dict(joints=np.array([[.1,.2],[.3,.4]]),contact_forces=np.ones((2,3)),fly=np.zeros((4,3)))
        kwargs=dict(time_s=0,vision_time_s=0,raw_vision=np.zeros((2,8,8,3)),previous_motor_command=np.zeros(2))
        a=from_flygym(SensoryStream(),observation=obs,**kwargs)
        obs.update(fly=np.full((4,3),999),reward=1000,target_direction=[1,0])
        b=from_flygym(SensoryStream(),observation=obs,**kwargs)
        np.testing.assert_array_equal(a.joint_angles_rad,b.joint_angles_rad)
        np.testing.assert_array_equal(a.rgb,b.rgb)
        self.assertFalse(hasattr(b,'reward')); self.assertFalse(hasattr(b,'position'))

    def test_invalid_values_and_layout_changes(self):
        for bad in (np.nan,-1,256):
            with self.assertRaises(ValueError): SensoryStream().update(**sample(image=np.full((2,8,8,3),bad)))
        s=SensoryStream(); s.update(**sample())
        with self.assertRaises(ValueError): s.update(**sample(.02,contact_forces=np.zeros((3,3))))

    def test_rest_is_default_even_with_turn_request(self):
        np.testing.assert_array_equal(rest_capable_drive(),[0,0])
        np.testing.assert_array_equal(rest_capable_drive(0,1),[0,0])
        np.testing.assert_array_equal(rest_capable_drive(1,-1),rest_capable_drive(1,1)[::-1])
        for args in ((-1,0),(1,2),(np.nan,0)):
            with self.assertRaises(ValueError): rest_capable_drive(*args)


if __name__=='__main__': unittest.main()
