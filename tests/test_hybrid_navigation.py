import unittest,inspect
import numpy as np
from flyplasticity.hybrid_navigation import population_turn,HybridNavigation,PreferenceField


class HybridNavigationTests(unittest.TestCase):
    def test_population_identity_rotation_and_reflection(self):
        for heading in np.linspace(-3,3,13):
            for error in np.linspace(-3,3,13):
                self.assertAlmostEqual(population_turn(heading,heading+error),np.sin(error),places=12)
                self.assertAlmostEqual(population_turn(-heading,-heading-error),-np.sin(error),places=12)

    def test_controller_no_label_or_location_interface(self):
        self.assertEqual(list(inspect.signature(HybridNavigation.step).parameters),['self','output_spikes','heading','wind_world','odor_load'])
        motor=HybridNavigation()
        np.testing.assert_array_equal(motor.step([0,0],0,[-1,0],0),[0,0])
        for k in range(100):u=motor.step([1,1],0,[0,-1],1)
        self.assertGreater(u[1],u[0]);self.assertLessEqual(max(u),.95)
        for k in range(200):u=motor.step([0,0],0,[0,-1],0)
        np.testing.assert_array_equal(u,[0,0])

    def test_invalid_inputs_rejected(self):
        for c,h,w in [([1],0,[1,0]),([0,-1],0,[1,0]),([1,1],float('nan'),[1,0]),([1,1],0,[1])]:
            with self.assertRaises(ValueError):HybridNavigation().step(c,h,w,1)

    def test_lower_inhibitory_output_increases_approach(self):
        low=HybridNavigation();high=HybridNavigation()
        for k in range(100):a=low.step([1,0],0,[-1,0],1);b=high.step([1,1],0,[-1,0],1)
        self.assertGreater(a.mean(),b.mean())

    def test_odor_swap_does_not_change_wind(self):
        f=PreferenceField([[6,3,1],[6,-3,1]]);g=PreferenceField(f.sources,True)
        p=np.array([3,1,1]);np.testing.assert_array_equal(f.wind(p),g.wind(p))
        np.testing.assert_array_equal(f.sample(p[None]),g.sample(p[None])[::-1])

    def test_gradients_match_finite_differences(self):
        f=PreferenceField([[6,3,1],[6,-3,1]],True);p=np.array([2.,1.,.8]);eps=1e-5
        actual=np.column_stack([(f.sample((p+eps*np.eye(3)[i])[None])[:,0]-f.sample((p-eps*np.eye(3)[i])[None])[:,0])/(2*eps) for i in range(3)])
        np.testing.assert_allclose(actual,f.gradients(p),rtol=1e-8,atol=1e-9)
