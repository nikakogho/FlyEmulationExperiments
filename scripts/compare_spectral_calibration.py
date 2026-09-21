"""Re-render archived body poses with an opt-in spectral reconstruction.

No neural model, physical integration, or interpolation of archived timestamps.
"""
from pathlib import Path
import argparse
import hashlib
import json
import numpy as np
from sensory_fixture import ROOT, make_fixture, sample_eyes
from flyplasticity.spectral import SpectralReceptors
from flyplasticity.spectral_calibration import CalibratedSpectralReceptors, SOURCE, overlap_scale


class CommonBandAdapter:
    """Preserve the recorded scene's 315-550 nm material spectra exactly."""
    def __init__(self, measured, wavelength_nm):
        self.measured, self.wavelength_nm = measured, wavelength_nm.copy()

    def excite(self, w, p):
        return self.measured.excite(w, p)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--recording', default='results/sensory_scene_v2')
    ap.add_argument('--out', required=True)
    args = ap.parse_args()
    src, out = ROOT/args.recording, ROOT/args.out
    out.mkdir(parents=True, exist_ok=False)
    source = json.loads((src/'report.json').read_text())
    for p, sha in source['source_sha256'].items():
        if hashlib.sha256((ROOT/p).read_bytes()).hexdigest() != sha:
            raise ValueError('Original recording source changed: '+p)
    with np.load(src/'replay.npz') as z: tape = {k:z[k] for k in z.files}
    with np.load(src/'sensors.npz') as z: recorded = z['eye_excitation'].copy()
    old, new = SpectralReceptors(), CalibratedSpectralReceptors()
    _, fly, sim, _, eye, retina, spectra, mapping, _ = make_fixture()
    indices = [0, 30, 75, 110, 130, 160, 210, 250, 300]
    previous, updated = [], []
    try:
        for i in indices:
            p = sim.physics
            for field in ('qpos', 'qvel', 'act'):
                getattr(p.data, field)[:] = tape[field][i]
            p.forward()
            before = p.get_state().copy()
            retina.receptors = old
            baseline, _ = sample_eyes(sim, fly, eye, retina, spectra, mapping)
            np.testing.assert_array_equal(baseline, recorded[i])
            retina.receptors = CommonBandAdapter(new, old.wavelength_nm)
            candidate, _ = sample_eyes(sim, fly, eye, retina, spectra, mapping)
            np.testing.assert_array_equal(p.get_state(), before)
            np.testing.assert_array_equal(candidate[..., 1], baseline[..., 1])
            np.testing.assert_array_equal(candidate[..., 2][retina.pale], baseline[..., 2][retina.pale])
            previous.append(baseline); updated.append(candidate)
            print(f'Re-rendered archived frame {i}; no integration', flush=True)
    finally:
        sim.close()
    previous, updated = np.array(previous), np.array(updated)
    short, long = new.provenance['bands']
    a = np.array(short['mean'])[27:, 4]  # Rh6 450-550 nm
    b = np.array(long['mean'])[:21, 1]
    development = np.arange(21)%2 == 0
    scale = overlap_scale(a[development], b[development])
    validation = ~development
    diagnostic = dict(split='Alternating overlap wavelengths; same source animals, not independent biological validation',
        development_scale=scale, validation_wavelength_nm=np.arange(450, 551, 5)[validation].tolist(),
        unscaled_validation_rmse=float(np.sqrt(np.mean((a[validation]-b[validation])**2))),
        scaled_validation_rmse=float(np.sqrt(np.mean((a[validation]-b[validation]*scale)**2))))
    dt = source['sensory_interval_s']
    report = dict(status='completed', neural_steps=0, physics_integration_steps=0,
        original_recording=args.recording, recorded_frames=indices, baseline_exact=True,
        spectral_reconstruction='Opt-in; approximate overlap joining; legacy renderer unchanged',
        source_sha256={str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in
            [SOURCE, ROOT/'flyplasticity/spectral_calibration.py', Path(__file__), src/'sensors.npz', src/'replay.npz']},
        alignment=new.alignment, rh6_overlap_diagnostic=diagnostic,
        changed_channels=['Rh1', 'yellow R8 (Rh6)'], unchanged_channels=['R7', 'pale R8 (Rh5)'],
        mean_excitation_before=previous.mean(axis=(0, 1, 2)).tolist(),
        mean_excitation_after=updated.mean(axis=(0, 1, 2)).tolist(),
        temporal_readiness=dict(recording_interval_s=dt, samples_per_10ms_delay=.01/dt,
            samples_per_20ms_peak=.02/dt, proposed_calibration_interval_s=.001,
            proposal_is_engineering_resolution_not_measured_fly_update_rate=True,
            calibrated_temporal_model=False,
            reason='Relative ERG scale lacks effective photons/s; no independent numeric voltage traces recovered yet.'),
        limitations=['Five-channel scenes still limited to 315-550 nm; Rh1/Rh6 alone support 315-700.',
            'Spectral shape reconstruction does not validate single-cell transduction, learning or welfare.',
            'Temporal paper figures recovered, but fitting their raster curves would not provide independent raw-trace validation.'])
    (out/'comparison.json').write_text(json.dumps(report, indent=2)+'\n')
    np.savez_compressed(out/'comparison.npz', time_s=tape['time_s'][indices], before=previous, after=updated)
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    fig, axes = plt.subplots(1, 2, figsize=(12, 4), constrained_layout=True)
    for c in ('Rh1', 'Rh6'):
        j = ('Rh1', 'Rh3', 'Rh4', 'Rh5', 'Rh6').index(c)
        curve = new.curves[c]
        line, = axes[0].plot(curve['wavelength_nm'], curve['response'], label=c+' reconstructed')
        axes[0].plot(old.wavelength_nm, old.response[:, j], '--', color=line.get_color(), label=c+' legacy')
    axes[0].set(xlabel='Wavelength (nm)', ylabel='Relative ERG shape (own peak = 1)', title='Recovered long-wavelength coverage')
    axes[0].legend(fontsize=8)
    for j, c in ((0, 'Rh1'), (2, 'R8 mosaic')):
        line, = axes[1].plot(tape['time_s'][indices], updated[..., j].mean(axis=(1, 2)), 'o-', label=c+' reconstructed')
        axes[1].plot(tape['time_s'][indices], previous[..., j].mean(axis=(1, 2)), 'o--', color=line.get_color(), label=c+' legacy')
    axes[1].set(xlabel='Archived scene time (s)', ylabel='Relative excitation proxy', title='Same body poses and material spectra')
    axes[1].legend(fontsize=8)
    fig.savefig(out/'comparison.png', dpi=160)
    print(json.dumps(report, indent=2))


if __name__ == '__main__': main()
