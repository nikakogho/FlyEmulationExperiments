import unittest
from unittest.mock import Mock
import numpy as np
from scipy.integrate import trapezoid
from flyplasticity.spectral import SpectralReceptors, SpectralRetina, narrowband, render_spectral_eyes
from flyplasticity.retinal_bridge import RetinalBridge
from flyplasticity.spectral_learning import receptor_features


class SpectralTests(unittest.TestCase):
    def setUp(self):
        self.r = SpectralReceptors()
        self.w = self.r.wavelength_nm

    def test_dark_additivity_and_exposure(self):
        a = narrowband(self.w, 365)
        b = narrowband(self.w, 450)
        np.testing.assert_array_equal(self.r.excite(self.w, a*0), np.zeros(5))
        np.testing.assert_allclose(self.r.excite(self.w, a+b), self.r.excite(self.w, a)+self.r.excite(self.w, b))
        np.testing.assert_allclose(self.r.excite(self.w, a*3), self.r.excite(self.w, a)*3)

    def test_spectral_selectivity_and_equal_photon_stimuli(self):
        stimuli = np.array([narrowband(self.w, c) for c in (365, 450, 525)])
        np.testing.assert_allclose(trapezoid(stimuli, self.w), 1)
        q = self.r.excite(self.w, stimuli)
        self.assertGreater(q[0, 1], q[1, 1])
        self.assertGreater(q[0, 2], q[2, 2])
        self.assertGreater(q[1, 3], q[2, 3])
        self.assertGreater(q[2, 4], q[1, 4])
        self.assertGreater(q[0, 0], 0)  # Broad outer receptors include UV response.

    def test_invalid_data_and_no_out_of_band_guess(self):
        for w, p in [([300, 350], [1, 1]), ([500, 600], [1, 1]),
                     ([400, 350], [1, 1]), ([350, 400], [-1, 1]),
                     ([350, 400], [np.nan, 1]), ([350, 400], [1, 2, 3])]:
            with self.assertRaises(ValueError): self.r.excite(w, p)

    def test_nonuniform_quadrature_constant_spectrum(self):
        w = np.array([350, 353, 410, 450])
        r = np.stack([np.interp(w, self.w, c) for c in self.r.response.T], axis=-1)
        expected = sum((w[i+1]-w[i])*(r[i]+r[i+1])/2 for i in range(3))
        np.testing.assert_allclose(self.r.excite(w, np.ones(4)), expected)

    def test_mosaic_preserves_actual_receptor_pairs_and_eye_independence(self):
        b = RetinalBridge(np.array([[1, 2], [3, 4]]), np.array([[0, 0], [0, 1], [1, 0], [1, 1]]))
        retina = SpectralRetina(b, seed=10)
        image = np.broadcast_to(np.arange(1, 6), (2, 2, 2, 5)).copy()
        image[1] = 0
        actual, potential = retina.sample_excitation(image)
        np.testing.assert_array_equal(actual[1], 0)
        np.testing.assert_array_equal(actual[0, :, 1], np.where(retina.pale[0], 2, 3))
        np.testing.assert_array_equal(actual[0, :, 2], np.where(retina.pale[0], 4, 5))
        np.testing.assert_array_equal(retina.pale, SpectralRetina(b, seed=10).pale)

    def test_visibility_occludes_spectral_source(self):
        p = Mock()
        p.model.ngeom = 2
        p.render.return_value = np.array([[[0, 5], [1, 5], [-1, -1]]])
        uv, blue = (narrowband(self.w, c) for c in (365, 450))
        output = render_spectral_eyes(p, ['L', 'R'], (1, 3), {0: uv, 1: blue}, uv*0, self.r)
        np.testing.assert_allclose(output[0, 0, 0], self.r.excite(self.w, uv))
        np.testing.assert_allclose(output[0, 0, 1], self.r.excite(self.w, blue))
        np.testing.assert_array_equal(output[0, 0, 2], 0)
        with self.assertRaises(ValueError):
            render_spectral_eyes(p, ['L'], (1, 3), {0: uv}, uv*0, self.r)

    def test_learning_adapter_retains_uv_and_both_r8_subtypes(self):
        pale = np.array([[True, False], [False, True]])
        background = np.ones((2, 2, 3))*.01
        image = background.copy()
        image[..., 1] += .02
        features = receptor_features(image, background, pale, gain=1)
        np.testing.assert_allclose(features[:, [1, 2]], .02)
        np.testing.assert_array_equal(features[:, [0, 3, 4]], 0)
        image = background.copy()
        image[..., 2] += .04
        features = receptor_features(image, background, pale, gain=1)
        np.testing.assert_allclose(features[:, [3, 4]], .04)
        np.testing.assert_array_equal(features[:, [0, 1, 2]], 0)
        np.testing.assert_array_equal(receptor_features(background, background, pale), 0)

    def test_published_data_anchor_and_normalization(self):
        # Independently inspected workbook E3 and E11: Rh1 315 nm and 355 nm.
        self.assertAlmostEqual(self.r.response[0, 0], 2.49595192455136/3.93216108457188)
        np.testing.assert_allclose(self.r.response.max(axis=0), 1)


if __name__ == '__main__': unittest.main()
