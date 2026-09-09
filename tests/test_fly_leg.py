import unittest
import numpy as np,pandas as pd
from flyplasticity.fly_leg_rig import FlyLegRig
from scripts.fanc_exact_pathway import join_targets


class FlyLegTests(unittest.TestCase):
    def test_action_angle_and_passive_settling(self):
        rig=FlyLegRig();initial=rig.observe()['anatomical_angle_deg']
        for _ in range(500):rig.step([1,0])
        flex=rig.observe()['anatomical_angle_deg'];self.assertLess(flex,initial)
        for _ in range(500):rig.step([0,1])
        self.assertGreater(rig.observe()['anatomical_angle_deg'],flex)
        for _ in range(500):rig.step([0,0])
        self.assertLess(abs(rig.data.qvel[0]),1e-6)
        self.assertEqual(rig.model.nq,1)
        self.assertEqual(rig.model.jnt_stiffness[0],0)

    def test_stop_and_neural_rejection(self):
        with self.assertRaises(ValueError):FlyLegRig(neural_model=object())
        r=FlyLegRig();before=r.data.qpos.copy()
        with self.assertRaises(RuntimeError):r.step([1,0],fault=True)
        with self.assertRaises(RuntimeError):r.step([1,0])
        np.testing.assert_array_equal(before,r.data.qpos);self.assertEqual(r.steps,0)

    def test_cell_mapping_preserves_ids_and_unknowns(self):
        a='648518346496932836';b='648518346496932837'
        e=pd.DataFrame(dict(post_pt_root_id=[a,b]));m=pd.DataFrame(dict(segID=[a],muscle=['main_tibia_flexor']))
        j=join_targets(e,m);self.assertEqual(j.muscle.iloc[0],'main_tibia_flexor');self.assertTrue(pd.isna(j.muscle.iloc[1]))
        with self.assertRaises(ValueError):join_targets(e,pd.concat([m,m]))
