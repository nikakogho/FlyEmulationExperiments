import unittest
import numpy as np
from flyplasticity.navigation_audit import contact_graph, shortest_paths, input_coverage


class NavigationAuditTests(unittest.TestCase):
    def test_directed_paths_and_unreachable(self):
        g=contact_graph(5,[0,1,2],[1,2,3],[2,3,4])
        self.assertEqual(shortest_paths(g,0,[0,3,4]),{0:[0],3:[0,1,2,3],4:None})
        self.assertIsNone(shortest_paths(g,3,[0])[0])

    def test_shortest_not_largest_contact_product(self):
        g=contact_graph(4,[0,0,1,2],[3,1,2,3],[1,100,100,100])
        self.assertEqual(shortest_paths(g,0,[3])[3],[0,3])

    def test_contact_conservation_with_duplicate_rows(self):
        g=contact_graph(3,[0,0,2],[1,1,1],[2,3,7])
        self.assertEqual(input_coverage(g,[0,1]),dict(total_contacts=12,
            internal_contacts=5,excluded_contacts=7,retained_fraction=5/12))

    def test_bad_anatomy_rejected(self):
        for pre,post,w in [([0],[1],[-1]),([0],[1],[float('nan')]),
                           ([0.5],[1],[1]),([3],[1],[1]),([0],[1],[1.5])]:
            with self.assertRaises(ValueError):contact_graph(3,pre,post,w)
