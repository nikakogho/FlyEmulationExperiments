import hashlib
from pathlib import Path
import tempfile
import unittest
import numpy as np
from flyplasticity.raw_motor_calibration import (
    recording_time, frame_indices, matlab_spike_indices, passive_pulse,
    aligned_probe, fit_probe_trials,
)
from flyplasticity.figure_twitch import twitch
from scripts.calibrate_raw_motor import verify_archive


class RawMotorCalibrationTests(unittest.TestCase):
    def test_matlab_sample_origin_and_bounds(self):
        t = recording_time({'sampratein': 10000, 'durSweep': .2, 'preDurInSec': .1}, 2000)
        self.assertEqual(t[0], -.1)
        self.assertEqual(t[1000], 0.)
        np.testing.assert_array_equal(matlab_spike_indices([1, 1001, 2000], 2000), [0, 1000, 1999])
        for bad in [[0], [2001], [1.5], [4, 3], [2, 2], [np.nan]]:
            with self.assertRaises(ValueError): matlab_spike_indices(bad, 2000)
        with self.assertRaises(ValueError): recording_time({'sampratein': 10000, 'durSweep': .2}, 1999)

    def test_exposure_uses_falling_edges_and_trims_tail(self):
        e = np.tile([0, 1, 1, 1, 0, 0, 0, 0, 0, 0], 8)
        idx, audit = frame_indices(e, 6)
        np.testing.assert_array_equal(idx, [3, 13, 23, 33, 43, 53])
        self.assertEqual(audit['trimmed_trailing_exposures'], 2)
        with self.assertRaises(ValueError): frame_indices(e, 10)
        with self.assertRaises(ValueError): frame_indices(e * .5, 6)

    def test_isolated_missing_frame_repair(self):
        e = np.tile([0, 1, 1, 1, 0, 0, 0, 0, 0, 0], 8)
        e[31:34] = 0
        idx, audit = frame_indices(e, 8)
        np.testing.assert_array_equal(idx, np.arange(3, 80, 10))
        self.assertEqual(audit['inserted_frames'], 1)

    def test_passive_resistance_units_offset_and_polarity(self):
        fs = 10000; t = np.arange(2000) / fs
        current = np.full_like(t, 6.); current[(t > .01) & (t < .06)] -= 5
        voltage = -47 + (current-6) * .328
        result = passive_pulse(current, voltage, fs)
        self.assertAlmostEqual(result['resistance_mohm'], 328)
        self.assertAlmostEqual(result['delta_voltage_mv'], -1.64)
        with self.assertRaises(ValueError): passive_pulse(-current, voltage, fs)
        with self.assertRaises(ValueError): passive_pulse(current, voltage[:-1], fs)

    def test_probe_alignment_and_area_to_linear_scale(self):
        n = 300; exposure = np.tile([0, 1, 1, 1, 0, 0, 0, 0, 0, 0], 30)
        com = np.full(29, 800.); com[10:] += 2
        trial = {'params': {'sampratein': 1000, 'durSweep': .3, 'preDurInSec': .1},
                 'voltage_1': np.zeros(n), 'spikes': [101], 'exposure': exposure,
                 'forceProbeStuff': {'CoM': com, 'EvalPnts': np.array([[0, 1, 2], [0, 0, 0]])}}
        tt, yy, _ = aligned_probe(trial)
        self.assertAlmostEqual(tt[np.where(yy > 0)[0][0]], 3.)
        self.assertTrue(np.allclose(yy[yy > 0], 2*np.sqrt(1.03)))
        trial['spikes'] = [101, 111]
        with self.assertRaises(ValueError): aligned_probe(trial)

    def test_known_twitch_recovered_across_different_frame_phases(self):
        traces = []
        for phase in [0., 1.5, 3.]:
            t = np.arange(-20., 120., 5.9) + phase
            traces.append((t, twitch(t, 3.6, 6., 2.)))
        fit = fit_probe_trials(traces)
        self.assertAlmostEqual(fit['amplitude_um'], 3.6, places=5)
        self.assertAlmostEqual(fit['time_to_peak_ms'], 14, places=5)
        self.assertFalse(fit['parameter_at_bound'])
        with self.assertRaises(ValueError): fit_probe_trials(traces[:2])

    def test_archive_verification_rejects_corruption(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / 'test.zip'; path.write_bytes(b'abc')
            digest = hashlib.sha256(b'abc').hexdigest()
            self.assertEqual(verify_archive(path, 3, digest), digest)
            with self.assertRaises(ValueError): verify_archive(path, 4, digest)
            path.write_bytes(b'abd')
            with self.assertRaises(ValueError): verify_archive(path, 3, digest)


if __name__ == '__main__':
    unittest.main()
