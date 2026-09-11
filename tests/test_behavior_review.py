import unittest
import numpy as np
from flyplasticity.behavior_review import ReviewedBehaviorMonitor


def sample(m,k,x,h=0,u=(.5,.5),enabled=True,source=1.):
    c=np.exp(-(x-source)**2/2)
    gradient=-(x-source)*c
    return m.observe(k*.01,[x,0,0],h,u,np.full((2,4),c),
        [[gradient,0,0],[gradient,0,0]],stimulus_enabled=enabled)


class BehaviorReviewTests(unittest.TestCase):
    def test_passby_is_logged_not_classified_as_withdrawal(self):
        m=ReviewedBehaviorMonitor();departure=False
        for k in range(101):departure|=any(sample(m,k,k*.04)['geometric_departure'])
        self.assertTrue(departure);self.assertFalse(m.stopped)

    def test_synthetic_withdrawal_stops_and_latches(self):
        m=ReviewedBehaviorMonitor()
        with self.assertRaises(RuntimeError):
            for k in range(101):sample(m,k,.04*k if k<=20 else .8-.04*(k-20),0 if k<=20 else np.pi,source=2.)
        self.assertEqual(m.reason,'stimulus_linked_withdrawal')
        with self.assertRaises(RuntimeError):sample(m,102,0)

    def test_blocked_effort(self):
        m=ReviewedBehaviorMonitor()
        with self.assertRaises(RuntimeError):
            for k in range(40):sample(m,k,0)
        self.assertEqual(m.reason,'blocked_effort')

    def test_turning_progress_is_not_blocked_translation(self):
        m=ReviewedBehaviorMonitor()
        for k in range(40):sample(m,k,0,h=k*.01,u=(.3,.7))
        self.assertFalse(m.stopped)

    def test_standing_transition_has_mechanical_grace(self):
        m=ReviewedBehaviorMonitor()
        for k in range(61):sample(m,k,min(k*.02,.2),u=(0,0),enabled=False)
        self.assertFalse(m.stopped)

    def test_persistent_failed_rest(self):
        m=ReviewedBehaviorMonitor()
        with self.assertRaises(RuntimeError):
            for k in range(61):sample(m,k,k*.01,u=(0,0),enabled=False)
        self.assertEqual(m.reason,'failed_rest')

    def test_competing_commands(self):
        m=ReviewedBehaviorMonitor()
        with self.assertRaises(RuntimeError):
            for k in range(61):sample(m,k,k*.003,u=(.7,.3) if k%4<2 else (.3,.7),enabled=False)
        self.assertEqual(m.reason,'competing_actions')

    def test_apparatus_off_does_not_count_as_departure(self):
        m=ReviewedBehaviorMonitor()
        for k in range(80):
            r=m.observe(k*.01,[k*.04,0,0],0,[.5,.5],np.full((2,4),.8 if k<30 else 0.),
                np.zeros((2,3)),stimulus_enabled=k<30)
            self.assertFalse(any(r['geometric_departure']))

    def test_missing_heading_gradient_and_stale_input_rejected(self):
        for h,g in [(float('nan'),np.zeros((2,3))),(0,None)]:
            with self.assertRaises(RuntimeError):ReviewedBehaviorMonitor().observe(0,[0,0,0],h,[0,0],np.zeros((2,4)),g,stimulus_enabled=False)
        m=ReviewedBehaviorMonitor();sample(m,0,0)
        with self.assertRaises(RuntimeError):sample(m,3,0)

    def test_rapid_departure_without_heading_reversal(self):
        m=ReviewedBehaviorMonitor()
        with self.assertRaises(RuntimeError):
            for k in range(101):
                t=k*.01;x=-1+2*t if t<=.4 else -.2+4*(t-.4)
                sample(m,k,x,u=(.3,.3) if t<=.4 else (.7,.7),source=0.)
        self.assertEqual(m.reason,'rapid_stimulus_departure')
