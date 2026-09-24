import json
from pathlib import Path
import unittest
import numpy as np
from flyplasticity.two_path_filter import path_rows
from flyplasticity.causal_filter import fit_ridge
from scripts.benchmark_two_path import select, training


class TwoPathTests(unittest.TestCase):
    def protocol(self):
        return json.loads((Path(__file__).resolve().parents[1]/'research/calibration/two_path_protocol.json').read_text())

    def test_order_and_independent_convolution(self):
        x = np.linspace(-.1, 3, 100)
        rows = path_rows(x, 'combined', 2)
        w = np.array([.1, .2, .3, -.1, .4, .7])
        z = np.sign(x)*np.log1p(abs(x)/.5)
        expected = (np.convolve(x, w[:3]) + np.convolve(z, w[3:]))[2:100]
        np.testing.assert_allclose(rows @ w, expected)
        np.testing.assert_array_equal(rows[:, :3], path_rows(x, 'linear', 2))

    def test_known_two_path_system_generalizes(self):
        rng = np.random.default_rng(17)
        x = path_rows(rng.uniform(-.05, 4, 3000), 'combined', 2)
        t = path_rows(rng.uniform(-.05, 4, 500), 'combined', 2)
        w = np.array([.1, .2, .3, -.1, .4, .7])
        model = fit_ridge(x, x @ w+2, 0.)
        np.testing.assert_allclose(model.predict(t), t @ w+2, atol=1e-11)

    def test_future_invariance(self):
        x = np.arange(200.)/100
        first = path_rows(x, 'combined')
        x[150:] += 100
        np.testing.assert_array_equal(first[:70], path_rows(x, 'combined')[:70])

    def test_invalid_kind_and_signal_rejected(self):
        for x, kind in [([1, 2, 3], 'other'), ([1, np.nan, 2], 'combined')]:
            with self.assertRaises(ValueError): path_rows(x, kind, 1)

    def test_selection_access_whitelist_and_block_boundaries(self):
        p = self.protocol()
        p['penalties'] = [.1]
        data = {}
        rng = np.random.default_rng(7)
        for hz in (20, 50):
            x = rng.uniform(0, 3, 2000)
            data[f'dc1_hz{hz}_stimulus'] = x
            data[f'dc1_hz{hz}_trials'] = np.repeat(x[:, None], 20, axis=1)
        # No held-out keys are present; any attempted access raises KeyError.
        result = select(data, p)
        self.assertEqual(set(result['chosen']), {'linear', 'compressed', 'combined'})
        x, y = training(data, p, 1, 'combined', [1400, 2000])
        self.assertEqual(x.shape, (1040, 162))
        self.assertEqual(x[0, 80], data['dc1_hz20_stimulus'][1400])
        self.assertAlmostEqual(y[0], data['dc1_hz20_trials'][1480, 0])


if __name__ == '__main__': unittest.main()
