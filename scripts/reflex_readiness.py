"""Record a mechanical null trial and M3 calibration gaps. Runs zero neurons."""
from pathlib import Path
import sys, json, hashlib
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
import numpy as np
import mujoco
from flyplasticity.fly_leg_rig import FlyLegRig
from flyplasticity.reflex_assay import Trace, compare_reflex


def main():
    import argparse
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--out', default='results/reflex_readiness')
    args = ap.parse_args()
    out = ROOT / args.out
    out.mkdir(exist_ok=False)
    rig = FlyLegRig()
    reference = rig.observe()['anatomical_angle_deg']
    # Initialize the mechanical fixture one degree more extended, at zero speed.
    # No neural tissue or neuron model receives this displacement.
    rig.data.qpos[0] -= np.deg2rad(1)
    mujoco.mj_forward(rig.model, rig.data)
    initial = rig.observe()
    rows = [initial]
    for _ in range(500):
        rows.append(rig.step([0, 0]))
    t = [r['time_s'] for r in rows]
    a = [r['anatomical_angle_deg'] for r in rows]
    trace = Trace(t, a, np.zeros(len(t)), np.zeros(len(t)))
    # A deliberately identical trace in all conditions must fail. This is a
    # software negative control, NOT three neural ablation experiments.
    null = compare_reflex(trace, trace, trace, reference_deg=reference, minimum_effect_deg=.1)
    report = dict(
        status='M3_incomplete_calibration_required', neural_steps=0,
        mechanical_steps=rig.steps, reference_angle_deg=reference,
        initial_displacement_deg=a[0]-reference, final_displacement_deg=a[-1]-reference,
        passive_correction_deg=abs(a[0]-reference)-abs(a[-1]-reference),
        identical_trace_negative_control=null,
        motor_id='648518346496932836', source_rank='3',
        unresolved=[
            'Exact motor ID to physiological slow/intermediate/fast identity',
            'Sensory response calibration; calcium cannot be silently converted to spikes',
            'Synapse efficacy, recruitment threshold, latency and force response',
            'Biological mechanics and independent held-out response validation',
            'Actual neural telemetry interpretation and protocol-specific limits'],
        welfare=dict(scope='mechanical_only', guard_events=len(rig.guard.events),
                     stop_events=sum(e['status']=='STOP' for e in rig.guard.events),
                     neural_assessment='not_run', modeled_needs_or_valence=False,
                     interpretation='Engineering checks only; not evidence of absence of suffering'),
        sources=[
            dict(url='https://elifesciences.org/articles/56754', role='motor recruitment and proprioceptive physiology'),
            dict(url='https://datadryad.org/dataset/doi:10.5061/dryad.dbrv15f6q',
                 role='candidate sensory calcium data; not fitted',
                 file_id=2453318, bytes=6113303,
                 expected_sha256='866e8487b51b8e2cbc1c9ec7d875a33f918249d14c76c115e37601b05cf59862',
                 access_observed_2026_09_09='metadata available; file stream HTTP403, API download HTTP401')],
        pathway_sha256=hashlib.sha256((ROOT/'results/fanc_exact_pathway/pathway.json').read_bytes()).hexdigest())
    (out/'report.json').write_text(json.dumps(report, indent=2))
    (out/'mechanical_null.json').write_text(json.dumps(rows))
    (out/'guard_events.json').write_text(json.dumps(rig.guard.events))
    print(json.dumps(report, indent=2))


if __name__ == '__main__': main()
