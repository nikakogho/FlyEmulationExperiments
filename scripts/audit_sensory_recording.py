"""Read-only verification of peripheral measurements against archived physics."""
from pathlib import Path
import argparse, hashlib, json, sys
import numpy as np
import mujoco
ROOT = Path(__file__).resolve().parents[1]; sys.path.insert(0, str(ROOT))
from flyplasticity.sensory_recording import scheduled_command


def audit(out):
    report = json.loads((out/'report.json').read_text())
    rows = json.loads((out/'telemetry.json').read_text())
    with np.load(out/'sensors.npz') as archive: a = {k:archive[k] for k in archive.files}
    with np.load(out/'replay.npz') as archive: tape = {k:archive[k] for k in archive.files}
    t = a['time_s']; m = mujoco.MjModel.from_binary_path(str(out/'scene.mjb')); d = mujoco.MjData(m)
    prefix = report['contact_names'][0].split('/')[0]
    joint_ids = [mujoco.mj_name2id(m, mujoco.mjtObj.mjOBJ_JOINT, f'{prefix}/{name}')
                 for name in report['joint_names']]
    if any(i < 0 for i in joint_ids): raise ValueError('Unmapped recorded joint')
    q_indices = m.jnt_qposadr[joint_ids]
    v_indices = m.jnt_dofadr[joint_ids]
    q_error = float(np.max(np.abs(tape['qpos'][:, q_indices]-a['joint_angles_rad'])))
    v_error = float(np.max(np.abs(tape['qvel'][:, v_indices]-a['joint_velocities_rad_s'])))
    positions = np.array([r['sensor_positions_mm'] for r in rows])
    expected_odor = np.exp(-np.linalg.norm(positions-np.array(report['odor_source_mm']), axis=-1)**2/32)
    odor_error = float(np.max(np.abs(a['odor_concentration'][:, 0]-expected_odor)))
    rest = t >= 2.7-1e-9
    xyz = np.array([r['xyz'] for r in rows]); speeds = np.array([r['speed_mm_s'] for r in rows])
    displacement = float(np.linalg.norm(xyz[rest][-1, :2]-xyz[rest][0, :2]))
    rest_speed = float(np.median(speeds[rest]))
    measured_previous = np.array([np.zeros(2) if i == 0 else scheduled_command((i-1)*.01) for i in range(len(t))])
    checks = dict(completed=report['status']=='completed', no_neural_execution=report['neural_steps']==0,
        all_samples_present=len(t)==301, timestamps=np.allclose(t, np.arange(301)*.01, atol=1e-9, rtol=0),
        all_acquisitions_synchronized=np.allclose(a['acquisition_s'], t[:, None], atol=1e-9, rtol=0),
        replay_times_equal=np.array_equal(t, tape['time_s']), finite=all(np.isfinite(x).all() for x in a.values()),
        finite_physics=all(np.isfinite(x).all() for x in tape.values()),
        actual_joint_positions=q_error<1e-5, actual_joint_velocities=v_error<1e-3,
        antenna_position_odor_consistency=odor_error<1e-6,
        previous_commands=np.array_equal(measured_previous, a['previous_command']),
        unchanged_sources=all(hashlib.sha256((ROOT/p).read_bytes()).hexdigest()==sha for p,sha in report['source_sha256'].items()),
        spatial_vision_retained=bool(np.min(np.std(a['eye_excitation'][:, :, :, 0], axis=2))>1e-5),
        nonzero_visual_input_during_rest=bool(np.all(a['eye_excitation'][rest].mean(axis=(1,2,3))>0)),
        nonzero_odor_during_rest=bool(np.all(a['odor_concentration'][rest]>0)),
        optical_change_during_movement=bool(np.max(np.abs(np.diff(a['eye_excitation'][30:211], axis=0)))>1e-5),
        final_rest_displacement=displacement<=.2, final_rest_speed=rest_speed<=.5,
        moved=float(np.linalg.norm(xyz[-1,:2]-xyz[0,:2]))>1.,
        turned=abs(float(np.unwrap([r['heading'] for r in rows])[160]-np.unwrap([r['heading'] for r in rows])[110]))>.1,
        **report['checks'])
    # These are numerical/mechanical tolerances, not physiological or welfare limits.
    result = dict(passed=all(checks.values()), checks={k:bool(v) for k,v in checks.items()},
        samples=len(t), eye_shape=list(a['eye_excitation'].shape), joint_count=len(q_indices),
        contact_count=a['contact_vectors_native'].shape[1],
        maximum_joint_position_error_rad=q_error, maximum_joint_velocity_error_rad_s=v_error,
        maximum_odor_error=odor_error, final_rest_displacement_mm=displacement,
        final_rest_median_speed_mm_s=rest_speed,
        displacement_mm=float(np.linalg.norm(xyz[-1,:2]-xyz[0,:2])),
        geometry_max_error_pixels=max(r['error_pixels'] for r in json.loads((out/'projection_checks.json').read_text())),
        new_neural_steps=0, new_physics_steps=0,
        limitation='Acquisition and simulator consistency only; no physiological transduction or subjective-welfare validation')
    (out/'audit.json').write_text(json.dumps(result, indent=2))
    return result


if __name__ == '__main__':
    ap=argparse.ArgumentParser(); ap.add_argument('--path', required=True); args=ap.parse_args()
    result=audit(ROOT/args.path); print(json.dumps(result, indent=2)); raise SystemExit(not result['passed'])
