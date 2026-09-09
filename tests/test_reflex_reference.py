import unittest
import numpy as np
import pandas as pd
from scripts.reflex_reference import anatomical_angle,type_lookup


class ReflexReferenceTests(unittest.TestCase):
    def test_angle_convention_and_invalid_geometry(self):
        self.assertAlmostEqual(anatomical_angle(np.array([[-1.,0,0],[0,0,0],[1,0,0]])),180)
        self.assertAlmostEqual(anatomical_angle(np.array([[-1.,0,0],[0,0,0],[0,1,0]])),90)
        with self.assertRaises(ValueError): anatomical_angle(np.zeros((3,3)))

    def test_ids_exact_and_ambiguity_not_silently_resolved(self):
        ids=['648518346489572037','648518346489572038']
        frame=pd.DataFrame(dict(pt_root_id=ids,cell_type=['claw_ext','claw_flex'],valid=['t','t']))
        mapping=type_lookup(frame)
        self.assertEqual(mapping[ids[0]],'claw_ext')
        self.assertEqual(len(mapping),2)
        bad=pd.concat([frame,pd.DataFrame(dict(pt_root_id=[ids[0]],cell_type=['club'],valid=['t']))])
        with self.assertRaises(ValueError): type_lookup(bad)
