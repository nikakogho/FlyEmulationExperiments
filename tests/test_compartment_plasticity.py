import unittest
import numpy as np
from flyplasticity.compartment_plasticity import CompartmentEligibilityLTD

class CompartmentTests(unittest.TestCase):
    def test_locality_and_frozen_readout(self):
        r=CompartmentEligibilityLTD([0,0],[0,1],{0:[1],1:[2]},3)
        w=np.ones(2)
        for _ in range(30):w=r.step([1,1,0],w)
        self.assertLess(w[0],1);self.assertEqual(w[1],1)
        before=w.copy()
        for _ in range(30):w=r.step([1,1,1],w,learn=False)
        np.testing.assert_array_equal(w,before)

    def test_explicit_mapping_required(self):
        with self.assertRaises(ValueError):CompartmentEligibilityLTD([0,0],[0,1],{0:[1]},3)

    def test_invalid_data_does_not_change_state(self):
        r=CompartmentEligibilityLTD([0],[0],{0:[1]},2)
        with self.assertRaises(ValueError):r.step([1,np.nan],[1])
        np.testing.assert_array_equal(r.rules[0][1].e,0)

if __name__=='__main__':unittest.main()
