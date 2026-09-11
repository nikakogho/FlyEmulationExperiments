import unittest
import numpy as np
from flygym.arena import OdorArena
from flyplasticity.visual_markers import noncolliding_odor_markers


class VisualMarkerTests(unittest.TestCase):
    def test_visuals_are_sites_and_cannot_be_explicit_contact_geometries(self):
        a=OdorArena(odor_source=np.array([[6,3,1],[6,-3,1]]),peak_odor_intensity=np.eye(2))
        self.assertEqual(noncolliding_odor_markers(a),2)
        self.assertEqual(len(a.root_element.find_all('geom')),1)
        self.assertEqual(len(a.root_element.find_all('site')),2)
