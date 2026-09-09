import unittest
import pandas as pd
from scripts.audit_malecns import select_candidates, incoming_edges
import pyarrow as pa


class AnatomyTests(unittest.TestCase):
    def test_edge_filter_and_count_conservation(self):
        batch = pa.record_batch({'body_pre':[1,2,3,4], 'body_post':[10,11,10,12], 'weight':[2,3,5,7]})
        edges, rows = incoming_edges([batch.slice(0,2),batch.slice(2)], [10])
        self.assertEqual(rows,4)
        self.assertEqual(edges.weight.sum(),7)
        self.assertEqual(edges.body_pre.tolist(),[1,3])
        self.assertEqual(set(edges.body_post),{10})

    def test_bad_edges_rejected(self):
        for value in [-1,None]:
            batch=pa.record_batch({'body_pre':[1], 'body_post':[10], 'weight':pa.array([value],type=pa.int64())})
            with self.assertRaises(ValueError):
                incoming_edges([batch],[10])

    def frame(self):
        common = dict(somaSide='L', rootSide=None, entryNerve=None,
                      mancBodyid=None, statusLabel='Reviewed')
        return pd.DataFrame([
            dict(common, bodyId=1, superclass='vnc_motor', subclass='fl',
                 type='Ti flexor MN', somaNeuromere='T1'),
            dict(common, bodyId=2, superclass='vnc_motor', subclass='hl',
                 type='Ti flexor MN', somaNeuromere='T3'),
            dict(common, bodyId=3, superclass='descending_neuron', subclass='fl',
                 type='Ti flexor MN', somaNeuromere='T1'),
            dict(common, bodyId=4, superclass='vnc_sensory', subclass='chordotonal organ',
                 type='unknown', somaNeuromere=None, entryNerve='ProLN'),
            dict(common, bodyId=5, superclass='vnc_sensory', subclass='taste bristle',
                 type='unknown', somaNeuromere=None, entryNerve='ProLN'),
            dict(common, bodyId=6, superclass='sensory_ascending', subclass='chordotonal organ',
                 type='unknown', somaNeuromere=None, entryNerve='ProCN'),
            dict(common, bodyId=7, superclass='vnc_motor', subclass='fl',
                 type='Ti flexor MN', somaNeuromere='T1', statusLabel='Not examined')])

    def test_excludes_wrong_leg_descending_and_taste_cells(self):
        motors, sensory = select_candidates(self.frame())
        self.assertEqual(motors.bodyId.tolist(), [1])
        self.assertEqual(sensory.bodyId.tolist(), [4, 6])
        self.assertTrue(motors.rootSide.isna().all())

    def test_duplicate_ids_and_missing_schema_rejected(self):
        df = self.frame()
        with self.assertRaises(ValueError):
            select_candidates(pd.concat([df, df]))
        with self.assertRaises(ValueError):
            select_candidates(df.drop(columns=['rootSide']))
