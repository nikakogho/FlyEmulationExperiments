import unittest
import numpy as np
from flyplasticity.learning_preflight import NeuralPreflightGuard, FixedPathwayAudit

class LearningPreflightTests(unittest.TestCase):
    def make(self, weights=(0., 0.), modulators=()):
        self.route = dict(pre=np.array([2, 2]), post=np.array([0, 1]),
                          weights=np.array(weights), modulatory_sources=modulators)
        audit = FixedPathwayAudit(3, [2], **self.route)
        return NeuralPreflightGuard(3, [2], pathways=audit)

    def observe(self, guard, t=0, counts=(0, 0, 0), reward=(0, 0, 0)):
        z = np.zeros(3)
        return guard.inspect(t, counts, z, z, z, reward, **self.route)

    def test_disabled_outputs_allow_spikes_but_record_them(self):
        g = self.make()
        row = self.observe(g, counts=(0, 0, 2))
        self.assertEqual(row['ppl1_spikes'], 2)
        self.assertEqual(row['ppl1_spikes_with_enabled_route'], 0)
        self.assertFalse(g.guard.stopped)

    def test_each_weight_sign_and_cancellation_trigger_latched_stop(self):
        for weights in [(1., 0.), (-1., 0.), (1., -1.)]:
            g = self.make(weights)
            self.observe(g)
            with self.assertRaises(RuntimeError): self.observe(g, .005, (0, 0, 1))
            self.assertEqual(g.guard.events[-1]['reason'], 'ppl1_activity_with_enabled_route')
            with self.assertRaises(RuntimeError): self.observe(g, .01)

    def test_modulatory_route_is_not_hidden_by_zero_synapses(self):
        g = self.make(modulators=(2,))
        with self.assertRaises(RuntimeError): self.observe(g, counts=(0, 0, 1))

    def test_unknown_routes_rejected(self):
        with self.assertRaises(ValueError): self.make(modulators=None)
        for field, value in [('weights', [np.nan, 0]), ('weights', [0]),
                             ('pre', [2, 1]), ('post', [1, 0]),
                             ('modulatory_sources', None), ('modulatory_sources', (2,))]:
            g = self.make()
            self.route[field] = value
            with self.assertRaises(RuntimeError): self.observe(g)
            self.assertTrue(g.guard.stopped)

    def test_route_activation_after_disconnected_spike_is_rejected(self):
        # Pending delayed spikes must not become effective after a weight edit.
        g = self.make()
        self.observe(g, counts=(0, 0, 1))
        self.route['weights'][0] = 1
        with self.assertRaises(RuntimeError): self.observe(g, .005)

    def test_missing_telemetry_or_unexpected_reward_rejected(self):
        for counts, reward in [([0, 0], [0, 0, 0]), ([0, 0, 0], [0, 1, 0]),
                               ([0, np.nan, 0], [0, 0, 0]), ([0, .5, 0], [0, 0, 0])]:
            g = self.make()
            with self.assertRaises(RuntimeError): self.observe(g, counts=counts, reward=reward)

    def test_recovery_quiet_and_clock(self):
        g = self.make()
        self.assertEqual(self.observe(g)['total_spikes'], 0)
        with self.assertRaises(RuntimeError): self.observe(g, .1)

    def test_population_activity_guard_still_stops(self):
        g = self.make()
        self.observe(g)
        with self.assertRaises(RuntimeError):
            for k in range(1, 13): self.observe(g, k*.005, (10, 10, 0))
        self.assertEqual(g.guard.events[-1]['reason'], 'persistent_high_activity')

if __name__ == '__main__': unittest.main()
