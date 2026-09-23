import unittest
import numpy as np
from flyplasticity.temporal_sampling import sampling_error, optical_gain


class TemporalSamplingTests(unittest.TestCase):
    def test_exact_constant_linear_and_native_sampling(self):
        for signal in [np.ones(101)*3, np.arange(101)*.25, np.sin(np.arange(101))]:
            stats,pred = sampling_error(signal,1)
            self.assertEqual(stats['rmse'],0)
            np.testing.assert_array_equal(pred, signal)
        for signal in [np.ones(101)*3, np.arange(101)*.25]:
            self.assertEqual(sampling_error(signal,10)[0]['rmse'],0)

    def test_no_extrapolated_endpoint(self):
        stats,pred = sampling_error(np.arange(104.),10)
        self.assertEqual(len(pred),101)
        self.assertEqual(stats['covered_samples'],101)
        self.assertEqual(stats['retained_samples'],11)

    def test_sampling_can_hide_oscillation(self):
        t=np.arange(201)*.0005
        y=np.sin(2*np.pi*100*t)
        bad,_=sampling_error(y,20)
        fine,_=sampling_error(y,2)
        self.assertGreater(bad['normalized_rmse'],.9)
        self.assertLess(fine['normalized_rmse'],.04)

    def test_gain_remains_positive_and_not_a_zero_baseline(self):
        gain=optical_gain(np.linspace(0,1,10001))
        self.assertGreaterEqual(gain.min(),.8-1e-12)
        self.assertLessEqual(gain.max(),1.2+1e-12)
        self.assertEqual(optical_gain(0),1.)

    def test_reject_unusable_series_and_stride(self):
        for a,k in [([1,2],1),([1,np.nan,3],1),([[1,2],[3,4]],1),
                    ([1,2,3],0),([1,2,3],10),([1,2,3],True),([1,2,3],1.5)]:
            with self.assertRaises(ValueError): sampling_error(a,k)
        with self.assertRaises(ValueError): optical_gain(np.inf)


if __name__ == '__main__': unittest.main()
