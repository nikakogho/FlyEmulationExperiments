import unittest
import numpy as np
from flyplasticity.causal_filter import causal_rows, fit_ridge, prediction_error
from flyplasticity.origin_data import ORIGIN_MISSING, numeric_column, trial_matrix, named_columns


class CausalFilterTests(unittest.TestCase):
    def test_lag_direction_no_wrap_and_no_future_access(self):
        x = np.arange(100.)
        rows = causal_rows(x, 3)
        np.testing.assert_array_equal(rows[0], [3, 2, 1, 0])
        np.testing.assert_array_equal(rows[-1], [99, 98, 97, 96])
        changed = x.copy()
        changed[51:] += 1000
        np.testing.assert_array_equal(causal_rows(changed, 3)[:48], rows[:48])

    def test_recovers_known_filter_on_independent_sequence(self):
        rng = np.random.default_rng(51)
        x, xt = rng.normal(size=5000), rng.normal(size=500)
        w = np.array([0., .3, .7, -.1])
        rows = causal_rows(x, 3)
        model = fit_ridge(rows, rows @ w + 2.4, 0.)
        np.testing.assert_allclose(model.weights, w, atol=1e-12)
        self.assertAlmostEqual(model.intercept, 2.4)
        test = causal_rows(xt, 3)
        self.assertLess(prediction_error(test @ w+2.4, model.predict(test))['rmse_mV'], 1e-12)

    def test_prediction_does_not_refit_to_new_input_distribution(self):
        x = np.arange(20.)[:, None]
        model = fit_ridge(x, 2*x[:, 0]+4, 0.)
        np.testing.assert_allclose(model.predict(x+100), 2*(x[:, 0]+100)+4)

    def test_block_slices_exclude_history_from_other_blocks(self):
        x = np.arange(2000.)
        fit = causal_rows(x[:1200], 80)
        val = causal_rows(x[1400:], 80)
        self.assertEqual(fit[-1, 0], 1199)
        self.assertEqual(val[0, 0], 1480)
        self.assertEqual(val[0, -1], 1400)
        self.assertLess(fit.max(), val.min())

    def test_shifted_training_fails_known_causal_task(self):
        rng = np.random.default_rng(9)
        x, test = rng.normal(size=2000), rng.normal(size=1000)
        w = np.array([0., 0., 1.])
        y = causal_rows(x, 2) @ w
        correct = fit_ridge(causal_rows(x, 2), y, 1e-6)
        wrong = fit_ridge(causal_rows(np.roll(x, 1000), 2), y, 1e-6)
        t = causal_rows(test, 2)
        self.assertLess(prediction_error(t @ w, correct.predict(t))['normalized_rmse'], 1e-5)
        self.assertGreater(prediction_error(t @ w, wrong.predict(t))['normalized_rmse'], .9)

    def test_reject_invalid_inputs(self):
        for x, lag in [([1, 2], 2), ([1, np.nan], 0), ([[1, 2]], 0), ([1, 2], True), ([1, 2], -1)]:
            with self.assertRaises(ValueError): causal_rows(x, lag)
        for x, y, penalty in [(np.ones((3, 1)), np.arange(3.), .1),
                              ([[1], [2]], [1], .1), ([[1], [2]], [1, 2], -1),
                              ([[1], [2]], [1, np.inf], .1)]:
            with self.assertRaises(ValueError): fit_ridge(x, y, penalty)
        for y, p in [([1, 1], [2, 2]), ([1, 2], [1]), ([1, 2], [1, np.nan])]:
            with self.assertRaises(ValueError): prediction_error(y, p)


class OriginDataTests(unittest.TestCase):
    def test_missing_sentinel_is_not_zero_or_an_observation(self):
        np.testing.assert_array_equal(numeric_column({'data':[0., 1., ORIGIN_MISSING]}, 2), [0, 1])
        for data in ([1, ORIGIN_MISSING, 3], [1, 2, 3], [1, np.nan], [1], [1, '2']):
            with self.assertRaises(ValueError): numeric_column({'data':data}, 2)

    def test_trials_follow_names_not_physical_column_order(self):
        columns = [{'name':'A', 'data':[1., 2.]}, {'name':'mean'}, {'name':'SD'}]
        columns += [{'name':f'n{i}', 'data':[i, i+1]} for i in range(20, 0, -1)]
        trials = trial_matrix({'columns':columns}, 2)
        np.testing.assert_array_equal(trials[0], np.arange(1, 21))
        columns.append(columns[-1])
        with self.assertRaises(ValueError): named_columns({'columns':columns})

    def test_reject_missing_trial_and_wrong_clock(self):
        cols = [{'name':'A', 'data':[1., 3.]}, {'name':'mean'}, {'name':'SD'}]
        cols += [{'name':f'n{i}', 'data':[i, i+1]} for i in range(1, 21)]
        with self.assertRaises(ValueError): trial_matrix({'columns':cols}, 2)
        with self.assertRaises(ValueError): trial_matrix({'columns':cols[:-1]}, 2)


if __name__ == '__main__':
    unittest.main()
