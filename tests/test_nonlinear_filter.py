import copy
import json
from pathlib import Path
import unittest
import numpy as np
from flyplasticity.nonlinear_filter import transform_light
from flyplasticity.causal_filter import causal_rows, fit_ridge
from scripts.benchmark_nonlinear_filter import select, validate_protocol, training_data


class NonlinearFilterTests(unittest.TestCase):
    def protocol(self):
        return json.loads((Path(__file__).resolve().parents[1]/'research/calibration/nonlinear_filter_protocol.json').read_text())

    def test_monotone_finite_zero_preserving_transforms(self):
        x = np.linspace(0, 5, 100)
        for c in self.protocol()['nonlinear_candidates']:
            y = transform_light(x, **c)
            self.assertTrue(np.isfinite(y).all())
            self.assertEqual(y[0], 0)
            self.assertTrue(np.all(np.diff(y) > 0))
        np.testing.assert_array_equal(transform_light(x, 'identity'), x)

    def test_reject_invalid_data_and_unknown_transforms(self):
        for x, kind, param in [([1, float('inf')], 'signed_power', .5), ([1, np.nan], 'signed_power', .5),
                ([[1, 2]], 'signed_power', .5), ([1, 2], 'signed_log1p', 0),
                ([1, 2], 'signed_power', np.inf), ([1, 2], 'unknown', 1),
                ([1, 2], 'identity', 2)]:
            with self.assertRaises(ValueError): transform_light(x, kind, param)

    def test_negative_source_values_are_preserved_without_clipping(self):
        x = np.array([-.04105, -.00982, 0., .00982, .04105])
        for c in self.protocol()['nonlinear_candidates']:
            y = transform_light(x, **c)
            self.assertTrue(np.all(np.diff(y) > 0))
            np.testing.assert_allclose(y, -y[::-1])
            self.assertLess(y[0], 0)

    def test_known_nonlinear_system_predicts_independent_signal(self):
        rng = np.random.default_rng(14)
        x, t = rng.uniform(0, 4, 2000), rng.uniform(0, 4, 400)
        w = np.array([.1, .4, .2])
        tx = causal_rows(transform_light(x, 'signed_log1p', .5), 2)
        model = fit_ridge(tx, tx @ w+1, 0.)
        test = causal_rows(transform_light(t, 'signed_log1p', .5), 2)
        np.testing.assert_allclose(model.predict(test), test @ w+1, atol=1e-12)

    def test_selection_cannot_access_evaluation_records(self):
        # A whitelist mapping raises on every access outside the declared development conditions.
        p = self.protocol()
        p['nonlinear_candidates'] = [dict(kind='signed_power', parameter=.5)]
        p['penalties'] = [.01]
        rng = np.random.default_rng(7)
        class Whitelist(dict):
            def __getitem__(self, name):
                if name not in self: raise AssertionError('Leaked evaluation key: '+name)
                return super().__getitem__(name)
        data = Whitelist()
        for hz in (20, 50):
            x = rng.uniform(.01, 2, 2000)
            y = np.sqrt(x)
            data[f'dc1_hz{hz}_stimulus'] = x
            data[f'dc1_hz{hz}_trials'] = np.repeat(y[:, None], 20, axis=1)
        result = select(data, p)
        self.assertLess(result['development_rmse_ratio'], .2)

    def test_transformed_future_cannot_change_past_predictions(self):
        x = np.arange(200.)/100
        a = causal_rows(transform_light(x, 'signed_log1p', .5), 80)
        x[150:] += 100
        b = causal_rows(transform_light(x, 'signed_log1p', .5), 80)
        np.testing.assert_array_equal(a[:70], b[:70])

    def test_split_validation_rejects_leakage(self):
        p = self.protocol()
        validate_protocol(p)
        for key, value in [('training_bandwidths', [20, 100]),
                           ('development_validation_slice', [1000, 2000]),
                           ('new_evaluation_background', 1), ('dt_ms', 10)]:
            broken = copy.deepcopy(p)
            broken[key] = value
            with self.assertRaises(ValueError): validate_protocol(broken)

    def test_training_windows_do_not_wrap_or_cross_blocks(self):
        p = self.protocol()
        data = {}
        for hz in (20, 50):
            data[f'dc1_hz{hz}_stimulus'] = np.arange(2000.)
            data[f'dc1_hz{hz}_trials'] = np.repeat(np.arange(2000.)[:, None], 20, axis=1)
        x, y = training_data(data, p, 1, dict(kind='signed_power', parameter=2), [1400, 2000])
        self.assertEqual(x[0, 0], 1480**2)
        self.assertEqual(x[0, -1], 1400**2)
        self.assertEqual(y[0], 1480)
        self.assertEqual(len(y), 1040)


if __name__ == '__main__': unittest.main()
