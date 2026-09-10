import unittest
import numpy as np
from flyplasticity.behavior_monitor import BehaviorMonitor

class BehaviorTests(unittest.TestCase):
    def test_stationary_rest_is_not_blocked_effort(self):
        m=BehaviorMonitor()
        for k in range(61):m.observe(k*.01,[0,0,0],[0,0],np.zeros((2,4)))
        self.assertFalse(m.stopped)

    def test_blocked_effort_and_latch(self):
        m=BehaviorMonitor()
        with self.assertRaises(RuntimeError):
            for k in range(31):m.observe(k*.01,[0,0,0],[.5,.5],np.zeros((2,4)))
        self.assertEqual(m.reason,'blocked_effort')
        with self.assertRaises(RuntimeError):m.observe(.4,[0,0,0],[0,0],np.zeros((2,4)))

    def test_moving_search_does_not_trigger_blocked_proxy(self):
        m=BehaviorMonitor()
        for k in range(61):m.observe(k*.01,[k*.05,0,0],[.5,.5],np.full((2,4),.2))
        self.assertFalse(m.stopped)

    def test_stimulus_linked_avoidance_on_synthetic_trace(self):
        m=BehaviorMonitor()
        with self.assertRaises(RuntimeError):
            for k in range(61):
                level=.1+.02*min(k,15)-.01*max(k-15,0)
                m.observe(k*.01,[k*.05,0,0],[.5,.5],np.full((2,4),max(0,level)))
        self.assertEqual(m.reason,'stimulus_linked_avoidance')

    def test_missing_and_stale_behavior_rejected(self):
        m=BehaviorMonitor();m.observe(0,[0,0,0],[0,0],np.zeros((2,4)))
        with self.assertRaises(RuntimeError):m.observe(.03,[0,0,0],[0,0],np.zeros((2,4)))
        with self.assertRaises(RuntimeError):BehaviorMonitor().observe(0,[0,0,0],[0,0],None)

    def test_competing_actions_on_synthetic_trace(self):
        m=BehaviorMonitor()
        with self.assertRaises(RuntimeError):
            for k in range(61):m.observe(k*.01,[k*.003,0,0],[.7,.3] if k%4<2 else [.3,.7],np.zeros((2,4)))
        self.assertEqual(m.reason,'competing_actions')

    def test_failure_to_rest_on_synthetic_trace(self):
        m=BehaviorMonitor()
        with self.assertRaises(RuntimeError):
            for k in range(31):m.observe(k*.01,[k*.01,0,0],[0,0],np.zeros((2,4)))
        self.assertEqual(m.reason,'failed_rest')

if __name__=='__main__':unittest.main()
