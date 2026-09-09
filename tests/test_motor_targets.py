import unittest
import pandas as pd
from scripts.resolve_motor_targets import exact_join,classify_mapping


class MotorTargetTests(unittest.TestCase):
    def test_target_and_laterality_conflicts_not_accepted(self):
        row=dict(type_malecns='Ti extensor MN',target='Tergotr.',somaSide='R',exit_nerve='VProN_R')
        self.assertEqual(classify_mapping(row),'target_conflict')
        row.update(target='Ti extensor',exit_nerve='ProLN_L')
        self.assertEqual(classify_mapping(row),'nerve_or_side_conflict')
        row['exit_nerve']='ProLN_R'
        self.assertEqual(classify_mapping(row),'consistent_published_assignment_confidence_unreported')
    def test_unmatched_is_unknown_not_name_matched(self):
        c=pd.DataFrame(dict(manc_id=['12704',None,'999'],type=['same']*3))
        t=pd.DataFrame(dict(bodyid=['12704'],target=['Ti extensor']))
        r=exact_join(c,t)
        self.assertEqual(r.target.iloc[0],'Ti extensor')
        self.assertTrue(r.target.iloc[1:].isna().all())

    def test_ambiguous_ids_rejected(self):
        c=pd.DataFrame(dict(manc_id=['1']))
        t=pd.DataFrame(dict(bodyid=['1','1'],target=['a','b']))
        with self.assertRaises(ValueError):exact_join(c,t)
