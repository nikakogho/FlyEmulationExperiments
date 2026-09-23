"""Fresh high-rate 3D optics at a fixed archived pose; no physics/neural steps."""
from pathlib import Path
import argparse
import hashlib
import json
import numpy as np
from sensory_fixture import ROOT, make_fixture, sample_eyes
from flyplasticity.temporal_sampling import optical_gain, sampling_error


def main():
    ap = argparse.ArgumentParser(); ap.add_argument('--out', required=True); args = ap.parse_args()
    out = ROOT/args.out; out.mkdir(parents=True, exist_ok=False)
    protocol_path = ROOT/'research/calibration/optical_timing_protocol.json'
    protocol = json.loads(protocol_path.read_text()); gates = protocol['gates']
    _, fly, sim, _, eye, retina, spectra, mapping, _ = make_fixture()
    archive = ROOT/'results/sensory_scene_v2/replay.npz'
    records, maximum_linearity = {}, 0.
    try:
        with np.load(archive) as tape:
            for key in ('qpos', 'qvel', 'act'): getattr(sim.physics.data, key)[:] = tape[key][0]
        sim.physics.forward(); initial = sim.physics.get_state().copy()
        base, _ = sample_eyes(sim, fly, eye, retina, spectra, mapping)
        # Each rate independently renders every eye frame at its own timestamps.
        for interval in protocol['intervals_s']:
            ticks = np.arange(round(protocol['duration_s']/interval)+1)
            # Integer microseconds ensure identical floating values at shared times.
            t = ticks*round(interval*1e6)/1e6
            frames = []
            for now in t:
                gain = float(optical_gain(now))
                frame, _ = sample_eyes(sim, fly, eye, retina,
                    {k:v*gain for k,v in spectra.items()}, {k:v*gain for k,v in mapping.items()})
                error = float(np.max(np.abs(frame-base*gain))/np.max(base))
                maximum_linearity = max(maximum_linearity, error)
                frames.append(frame)
                np.testing.assert_array_equal(sim.physics.get_state(), initial)
            key = str(round(interval*1e6))
            records[key] = (t, np.array(frames))
            print(f'Rendered {len(t)} fresh eye frames at {interval*1000:g} ms; no neural steps', flush=True)
    finally:
        sim.close()
    high_t, high = records['500']
    for key, stride in [('1000', 2), ('10000', 20)]:
        np.testing.assert_array_equal(records[key][0], high_t[::stride])
        np.testing.assert_array_equal(records[key][1], high[::stride])
    y = high.mean(axis=(1,2,3))
    errors = {key:sampling_error(y, stride)[0] for key,stride in [('1ms',2),('10ms',20)]}
    checks = dict(coincident_samples_exact=True, physical_state_unchanged=True,
        linearity=maximum_linearity <= gates['full_retina_relative_linearity_error_max'],
        one_ms_convergence=errors['1ms']['normalized_rmse'] <= gates['one_ms_interpolation_rmse_over_modulation_sd_max'],
        improvement=errors['1ms']['rmse'] < errors['10ms']['rmse'])
    for key,(t,values) in records.items(): np.savez_compressed(out/f'optics_{key}us.npz', time_s=t, excitation=values)
    report = dict(passed=all(checks.values()), checks=checks, neural_steps=0, physics_steps=0,
        fresh_eye_frame_pairs=sum(len(t) for t,_ in records.values()),
        maximum_relative_linearity_error=maximum_linearity, sampling_errors=errors,
        model='Legacy common-band static ERG spectral proxy, 315-550 nm',
        pose='Archived fixed rest pose; no body motion in this fixture',
        code_sha256={str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in
            [Path(__file__), protocol_path, archive, ROOT/'flyplasticity/temporal_sampling.py']},
        limitation='Optical acquisition convergence only; no calibrated voltage response, learning or welfare claim')
    (out/'checks.json').write_text(json.dumps(report, indent=2)+'\n')
    if not report['passed']: raise RuntimeError('Optical timing gate failed; preserve outputs')
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    fig, ax = plt.subplots(figsize=(10,4), constrained_layout=True)
    for key, label in [('500','0.5 ms'), ('1000','1 ms'), ('10000','10 ms')]:
        t,a = records[key]; ax.plot(t*1000, a.mean(axis=(1,2,3)), '.-', label=label)
    ax.set(xlabel='Optical clock (ms)', ylabel='Mean relative receptor excitation', title='Fresh 3D optical acquisition; fixed body, no brain')
    ax.legend(); fig.savefig(out/'timing.png', dpi=150)
    print(json.dumps(report, indent=2))


if __name__ == '__main__': main()
