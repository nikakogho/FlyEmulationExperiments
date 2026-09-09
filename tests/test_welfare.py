import unittest
from dataclasses import replace
from flyplasticity.welfare import Limits, Sample, Guard


class WelfareTests(unittest.TestCase):
    def setUp(self):
        self.guard = Guard(Limits(1., .1, 10., .2))
        self.quiet = Sample(0., 1., True, True, False, False)

    def test_stop_prevents_callback_and_latches(self):
        called = []
        with self.assertRaises(RuntimeError):
            self.guard.advance(replace(self.quiet, negative_state=True), lambda: called.append(1))
        with self.assertRaises(RuntimeError):
            self.guard.advance(self.quiet, lambda: called.append(1))
        self.assertEqual(called, [])

    def test_unknown_and_invalid_fail_closed(self):
        for sample in [None, replace(self.quiet, negative_state=None),
                       replace(self.quiet, activity=float('nan')),
                       replace(self.quiet, time_s=float('inf')),
                       replace(self.quiet, rest_available=False),
                       replace(self.quiet, sensors_coherent=False)]:
            with self.subTest(sample=sample):
                self.assertEqual(Guard(self.guard.limits).observe(sample)['status'], 'STOP')

    def test_persistence_and_recovery(self):
        for t in [0., .1]:
            self.assertEqual(self.guard.observe(replace(self.quiet, time_s=t, blocked_effort=True))['status'], 'WATCH')
        self.assertEqual(self.guard.observe(replace(self.quiet, time_s=.2))['status'], 'CONTINUE')
        for t in [.3, .4]:
            self.guard.observe(replace(self.quiet, time_s=t, activity=11.))
        self.assertEqual(self.guard.observe(replace(self.quiet, time_s=.5, activity=11.))['reason'], 'persistent_high_activity')

    def test_blocked_effort_stops_at_boundary(self):
        for t in [0., .1, .2]:
            result = self.guard.observe(replace(self.quiet, time_s=t, blocked_effort=True))
        self.assertEqual(result['reason'], 'persistent_blocked_effort')

    def test_time_gap_duplicate_and_missing_start(self):
        for t in [0., .11, -.1]:
            guard = Guard(self.guard.limits)
            guard.observe(self.quiet)
            self.assertEqual(guard.observe(replace(self.quiet, time_s=t))['status'], 'STOP')
        self.assertEqual(Guard(self.guard.limits).observe(replace(self.quiet, time_s=.1))['status'], 'STOP')

    def test_budget_stops_without_extra_step(self):
        calls = []
        for i in range(10):
            self.guard.advance(replace(self.quiet, time_s=i/10), lambda: calls.append(1))
        with self.assertRaises(RuntimeError):
            self.guard.advance(replace(self.quiet, time_s=1.), lambda: calls.append(1))
        self.assertEqual(len(calls), 10)

    def test_invalid_limits(self):
        for value in [0, -1, float('nan'), float('inf')]:
            with self.assertRaises(ValueError):
                Limits(value, .1, 10, .2)


if __name__ == '__main__':
    unittest.main()
