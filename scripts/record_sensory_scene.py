"""Three-second mechanical multisensory recording. No connectome execution."""
from pathlib import Path
import argparse, hashlib, json, sys, time
import numpy as np
import mujoco
from dm_control.mujoco.wrapper.core import MjvOption
from sensory_fixture import ROOT, make_fixture, sample_eyes, visual_contact_check
from flyplasticity.sensory_recording import SpectralBodyStream, project_world, scheduled_command


def calibrate_projection(sim, fly, eye):
    """Render known isolated targets through actual installed eye cameras."""
    p = sim.physics; m = p.model
    probe = m.name2id('sensor_calibration_probe', 'geom')
    pos, size = m.geom_pos[probe].copy(), m.geom_size[probe].copy()
    option = MjvOption(); option.geomgroup[:] = 0; option.geomgroup[5] = 1
    h, w = eye.ommatidia_id_map.shape
    rows = []
    try:
        for side in ('L', 'R'):
            name = f'{fly.name}/{side}Eye_cam'; cam = m.name2id(name, 'camera')
            origin = p.data.cam_xpos[cam].copy(); rotation = p.data.cam_xmat[cam].reshape(3, 3).copy()
            for dx, dy in ((0, 0), (.35, 0), (-.35, 0), (0, .35), (0, -.35)):
                for depth in (3., 6.):
                    target = origin+rotation@np.array([dx*depth, dy*depth, -depth])
                    m.geom_pos[probe] = target; m.geom_size[probe, 0] = .025*depth
                    p.forward()
                    seg = p.render(height=h, width=w, camera_id=name, segmentation=True, scene_option=option)
                    mask = (seg[..., 1] == 5) & (seg[..., 0] == probe)
                    if not mask.any(): raise ValueError('Calibration target not visible')
                    measured = np.argwhere(mask).mean(axis=0)
                    expected = project_world(target, origin, rotation, m.cam_fovy[cam], (h, w))
                    rows.append(dict(eye=side, dx=dx, dy=dy, depth_mm=depth,
                        expected_rc=expected.tolist(), measured_rc=measured.tolist(),
                        error_pixels=float(np.linalg.norm(measured-expected))))
    finally:
        m.geom_pos[probe] = pos; m.geom_size[probe] = size; p.forward()
    if max(r['error_pixels'] for r in rows) > 1.5:
        raise ValueError('Eye projection differs from analytic geometry by >1.5 pixels')
    return rows


def main():
    ap = argparse.ArgumentParser(); ap.add_argument('--out', required=True); args = ap.parse_args()
    out = ROOT/args.out; out.mkdir(parents=True, exist_ok=False)
    started = time.perf_counter()
    arena, fly, sim, obs, eye, retina, spectra, mapping, names = make_fixture()
    rows, packets, frames, checks = [], [], [], {}
    status, error = 'running', None
    try:
        visual_ids = visual_contact_check(sim)
        checks['visuals_excluded_from_collision_pairs'] = True
        for _ in range(3000):
            obs, _, end, trunc, _ = sim.step([0., 0.])
            if end or trunc: raise RuntimeError('Settling terminated')
        origin = sim.curr_time
        projection = calibrate_projection(sim, fly, eye)
        (out/'projection_checks.json').write_text(json.dumps(projection, indent=2))
        checks['actual_eye_projection'] = True
        # At one identical physical state, repeat optics and change only human colors.
        first, _ = sample_eyes(sim, fly, eye, retina, spectra, mapping)
        repeated, _ = sample_eyes(sim, fly, eye, retina, spectra, mapping)
        np.testing.assert_array_equal(first, repeated)
        colors = sim.physics.model.geom_rgba.copy()
        try:
            sim.physics.model.geom_rgba[:, :3] = np.random.default_rng(9).random((sim.physics.model.ngeom, 3))
            recolored, _ = sample_eyes(sim, fly, eye, retina, spectra, mapping)
            np.testing.assert_array_equal(first, recolored)
        finally: sim.physics.model.geom_rgba[:] = colors
        checks.update(repeated_optics_exact=True, independent_of_display_rgb=True)
        sim.physics.model.save_binary(str(out/'scene.mjb'))
        stream = SpectralBodyStream(.01); previous = np.zeros(2)
        for k in range(301):
            t = k*.01
            if abs(sim.curr_time-origin-t) > 1e-8 or abs(sim.physics.data.time-origin-t) > 1e-8:
                raise RuntimeError('Physical/acquisition clocks disagree')
            # Fresh observations and optics at this exact state, no intervening step.
            obs = sim.get_observation()
            actual, _ = sample_eyes(sim, fly, eye, retina, spectra, mapping)
            packet = stream.update(time_s=t, acquisition_s=[t]*4, eye_excitation=actual,
                joint_angles_rad=obs['joints'][0], joint_velocities_rad_s=obs['joints'][1],
                contact_vectors_native=obs['contact_forces'], odor_concentration=obs['odor_intensity'],
                previous_command=previous)
            packets.append(packet)
            p = sim.physics
            positions = p.bind(fly._antennae_sensors).sensordata.reshape(4, 3).copy()
            # Evaluator information is kept separate from peripheral packet fields.
            rows.append(dict(time_s=t, xyz=obs['fly'][0].tolist(),
                speed_mm_s=float(np.linalg.norm(obs['fly'][1, :2])),
                heading=float(np.arctan2(obs['fly_orientation'][1], obs['fly_orientation'][0])),
                sensor_positions_mm=positions.tolist(), previous_command=previous.tolist()))
            frames.append((t, p.data.qpos.copy(), p.data.qvel.copy(), p.data.act.copy()))
            if k == 300: break
            command = scheduled_command(t)
            for _ in range(100):
                obs, _, end, trunc, _ = sim.step(command)
                if end or trunc or not np.isfinite(p.get_state()).all():
                    raise RuntimeError('Invalid mechanical state')
                if any(int(c.geom1) in visual_ids or int(c.geom2) in visual_ids for c in p.data.contact):
                    raise RuntimeError('Unexpected visual contact')
            previous = command
            if k % 100 == 0: print(f'Recorded {t:.2f}s; no brain', flush=True)
        checks['no_visual_contacts_during_walk'] = True
        status = 'completed'
    except Exception as exc:
        status, error = 'failed', repr(exc)
        raise
    finally:
        metadata = dict(status=status, error=error, neural_steps=0, neural_model_connected=False,
            physical_warmup_s=.3, recorded_duration_s=rows[-1]['time_s'] if rows else 0,
            physics_timestep_s=.0001, sensory_interval_s=.01, seed=101,
            protocol='rest 0-.3; forward .3-1.1; turn 1.1-1.6; forward 1.6-2.1; rest 2.1-3 s',
            sensory_stimuli_continuous_during_rest=True, spectral_channels=['outer_Rh1', 'R7', 'R8'],
            spectral_support_nm=[315, 550], receptor_units='relative excitation from normalized ERG shapes',
            odor='one synthetic static Gaussian tracer, sigma 4 mm; no named receptor calibration',
            odor_source_mm=arena.source.tolist(), odor_sensor_order=['L palp', 'R palp', 'L antenna', 'R antenna'],
            contact_units='native FlyGym mechanical force units; no firing-rate conversion',
            joint_names=list(fly.monitored_joints), contact_names=list(fly.contact_sensor_placements),
            geometry_materials=names, material_spectra={k:v.tolist() for k,v in spectra.items()},
            wavelength_nm=retina.receptors.wavelength_nm.tolist(),
            unavailable=list(packets[0].unavailable) if packets else [],
            checks=checks, wall_seconds=time.perf_counter()-started,
            limitation='Mechanical fixture and spectral sampling; not physiological transduction, learning or a welfare assessment')
        sources=['scripts/record_sensory_scene.py', 'scripts/sensory_fixture.py',
            'flyplasticity/sensory_recording.py', 'flyplasticity/standing.py',
            'flyplasticity/spectral.py', 'flyplasticity/retinal_bridge.py',
            'data/spectral/receptor_curves.npz', 'results/visual_learning_path/flyvis_receptor_centers.json',
            '.venv/Lib/site-packages/flygym/fly.py', '.venv/Lib/site-packages/flygym/arena/base.py']
        metadata['source_sha256']={s:hashlib.sha256((ROOT/s).read_bytes()).hexdigest() for s in sources}
        (out/'report.json').write_text(json.dumps(metadata, indent=2))
        (out/'telemetry.json').write_text(json.dumps(rows, separators=(',', ':')))
        if packets:
            np.savez_compressed(out/'sensors.npz', **{name:np.array([getattr(p, name) for p in packets])
                for name in ('time_s', 'acquisition_s', 'eye_excitation', 'joint_angles_rad',
                             'joint_velocities_rad_s', 'contact_vectors_native', 'odor_concentration', 'previous_command')},
                pale=retina.pale, retinal_centers_rc=retina.bridge.centers[retina.bridge.to_target])
            np.savez_compressed(out/'replay.npz', time_s=[f[0] for f in frames], qpos=[f[1] for f in frames],
                qvel=[f[2] for f in frames], act=[f[3] for f in frames])
        sim.close()
        print(json.dumps(dict(status=status, error=error, samples=len(packets), checks=checks), indent=2))


if __name__ == '__main__': main()
