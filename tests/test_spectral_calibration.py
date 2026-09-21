import json
import unittest
import numpy as np
from flyplasticity.spectral import SpectralReceptors, narrowband
from flyplasticity.spectral_calibration import CalibratedSpectralReceptors, SOURCE, overlap_scale, pooled_sd


class SpectralCalibrationTests(unittest.TestCase):
    def setUp(self):
        self.r = CalibratedSpectralReceptors()

    def test_published_long_band_anchors_and_absent_tails(self):
        short, long = json.loads(SOURCE.read_text())['bands']
        self.assertEqual(long['wavelength_nm'], list(range(450, 701, 5)))
        # Workbook P3, R3; independently inspected before implementing extraction.
        np.testing.assert_allclose(long['mean'][0], [4.50555381487865, .980709553954951])
        self.assertEqual(long['channels'], ['Rh1', 'Rh6'])
        self.assertEqual(short['cells'], 'D3:N50')
        self.assertEqual(long['cells'], 'O3:S53')
        self.assertEqual(self.r.curves['Rh6']['wavelength_nm'][-1], 700)
        self.assertEqual(self.r.curves['Rh3']['wavelength_nm'][-1], 550)

    def test_no_unmeasured_zero_tails_or_silent_channel_drop(self):
        w = np.arange(550, 701, 5)
        with self.assertRaisesRegex(ValueError, 'Rh3'):
            self.r.excite(w, np.ones_like(w))
        q = self.r.excite(w, narrowband(w, 600), channels=('Rh1', 'Rh6'))
        self.assertEqual(q.shape, (2,))
        self.assertGreater(q[1], q[0])
        with self.assertRaises(ValueError):
            self.r.excite([700, 705], [0, 0], channels=('Rh6',))

    def test_pooled_uncertainty_matches_individual_samples(self):
        a, b = np.array([1, 2, 3, 4, 5, 6.]), np.array([4, 5, 6, 7, 8, 9.])
        result = pooled_sd(a.mean(), a.std(ddof=1), b.mean(), b.std(ddof=1))
        self.assertAlmostEqual(result, np.r_[a, b].std(ddof=1))

    def test_scale_and_normalization_do_not_claim_absolute_gain(self):
        self.assertAlmostEqual(overlap_scale([2, 4, 6], [1, 2, 3]), 2.)
        self.assertEqual(self.r.alignment['Rh1']['scale'], .5777)
        for c in self.r.curves.values():
            self.assertEqual(c['response'].max(), 1.)
            self.assertTrue(np.all(c['relative_sd'] >= 0))
        rh6 = self.r.curves['Rh6']
        self.assertEqual(rh6['wavelength_nm'][rh6['response'].argmax()], 600.)

    def test_short_only_channels_unchanged(self):
        old = SpectralReceptors()
        for j, name in ((1, 'Rh3'), (2, 'Rh4'), (3, 'Rh5')):
            np.testing.assert_array_equal(old.response[:, j], self.r.curves[name]['response'])
        self.assertEqual(old.wavelength_nm[-1], 550)
        self.assertEqual(old.response[-1, 4], 1.)

    def test_linearity_nonuniform_grid_and_channel_order(self):
        w = np.array([450., 463., 501., 580., 600., 647., 700.])
        a, b = np.arange(len(w)), np.ones(len(w))
        q = lambda p: self.r.excite(w, p, channels=('Rh6', 'Rh1'))
        np.testing.assert_allclose(q(a+b), q(a)+q(b))
        np.testing.assert_allclose(q(3*a), 3*q(a))
        np.testing.assert_array_equal(q(a*0), [0, 0])
        curves = np.array([np.interp(w, self.r.curves[c]['wavelength_nm'], self.r.curves[c]['response']) for c in ('Rh6', 'Rh1')])
        expected = np.sum(np.diff(w)[None, :]*(curves[:, :-1]+curves[:, 1:])/2, axis=1)
        np.testing.assert_allclose(q(b), expected)

    def test_reject_invalid_spectra_and_channels(self):
        for w, p in [([450, 450], [1, 1]), ([600, 550], [1, 1]),
                     ([450, 500], [1, -1]), ([450, 500], [1, np.nan]),
                     ([450, np.inf], [1, 1]), ([450, 500], [1])]:
            with self.assertRaises(ValueError): self.r.excite(w, p)
        for channels in [(), ('Rh6', 'Rh6'), ('unknown',)]:
            with self.assertRaises(ValueError): self.r.excite([450, 500], [1, 1], channels)


if __name__ == '__main__': unittest.main()
