import unittest
from flyplasticity.preference_evaluation import preference,assess


class PreferenceEvaluationTests(unittest.TestCase):
    def test_identity_swap_reverses_index(self):
        rows=[dict(time_s=k*.005,odor=[[.8]*4,[.2]*4]) for k in range(601)]
        self.assertAlmostEqual(preference(rows,'A')['index'],.6)
        self.assertAlmostEqual(preference(rows,'B')['index'],-.6)

    def test_missing_samples_or_trials_do_not_count_as_zero(self):
        with self.assertRaises(ValueError):preference([], 'A')
        self.assertFalse(assess([])['passed'])

    def test_controls_and_recovery_are_required(self):
        def r(x):return dict(completed=True,recovery_pass=True,weights_unchanged=True,displacement_mm=2,preference=dict(index=x))
        cases=[dict(probes=dict(pre=r(0),paired=r(.2),unpaired=r(.01),frozen=r(0))) for _ in range(4)]
        self.assertTrue(assess(cases)['passed'])
        cases[0]['probes']['paired']['recovery_pass']=False
        self.assertFalse(assess(cases)['passed'])

    def test_large_shared_shift_is_not_learning(self):
        def r(x):return dict(completed=True,recovery_pass=True,weights_unchanged=True,displacement_mm=2,preference=dict(index=x))
        cases=[dict(probes={k:r(0 if k=='pre' else .5) for k in ('pre','paired','unpaired','frozen')}) for _ in range(4)]
        self.assertFalse(assess(cases)['passed'])
