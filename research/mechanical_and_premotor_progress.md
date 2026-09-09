# Mechanical fixture and premotor audit

2026-09-09. No MaleCNS neural dynamics or embodied fly rollout executed.

## Mechanical execution result

Built a standalone MuJoCo hinge fixture with two antagonistic, filtered torque
actuators, passive spring/damping and the execution guard. It contains no neurons,
learning, modeled needs or valence. Its constructor rejects neural attachment.
The fixture uses arbitrary engineering SI parameters listed in
`flyplasticity/joint_rig.py`, not measured fly geometry, muscle forces or Hill
muscle dynamics. This is progress on M2 integration, not completion of biological
muscle mapping or of the proposed live interactive viewer.

Five integration tests verify opposing action, cancellation/rest, bounded force,
passive return, fault-stop latching, unchanged state after a stop, invalid-command
rejection, neural-attachment rejection and observation invariance. The complete
offline suite passes 67 tests. The test log is
`results/joint_rig/unit_tests.log`.

A 3-second, 3,000-step mechanical run renders positive activation, negative
activation and passive rest. Its trajectory exactly matches an unrendered
reference. At the end a synthetic sensory-coherence fault prevents another
physics step. The video holds the frozen final state and displays STOP. Telemetry,
guard events and an explicit result report are saved beside the video. No
automatic retry occurs. The 100-frame encoded video was decoded for verification.

These checks establish mechanical/software behavior. They are not evidence that
a neural model is comfortable. The activity field in this fixture explicitly
means actuator activation, not neural firing. Its thresholds must never be
copied into a live neural protocol as biological welfare limits. Legacy fly
simulation scripts remain outside this guard integration.

Run a fresh output:

```powershell
.venv/Scripts/python.exe scripts/run_joint_rig.py --out results/joint_rig_repeat
```

## Premotor connectivity result

The audit includes every annotated VNC-intrinsic neuron with a recorded edge to
the 14 selected tibia motor candidates, rather than selecting only the largest
few edges. It identifies **1,120 premotor candidates** providing **26,154 contacts
(79.03%)** of recorded motor input. **293** have incoming contacts from the
selected foreleg chordotonal pool.

However, 66.35% of the recorded input to those premotor candidates originates
outside the expanded motor/sensory/premotor pool. Adding one layer therefore does
not close the circuit. Neither percentage is a measure of functional influence
or a minimum completeness threshold for modeling a particular behavior.

Consensus transmitter predictions are 654 acetylcholine, 263 GABA, 198 glutamate
and 5 unclear. These remain predictions; receptor-dependent effects and
physiological synaptic strengths are not inferred from labels alone. In
particular, glutamate must not be assigned a universal sign.

The recorded evidence is in `results/premotor_audit/report.json`,
`premotor_candidates.json` and `sensory_to_premotor_edges.json`. Source version,
URL and transmitter-file hash are recorded; the preceding audit records the
annotation/graph hashes. Data come from the
[official MaleCNS download release](https://male-cns.janelia.org/download/).

```powershell
.venv/Scripts/python.exe scripts/audit_malecns.py --download-connectivity
.venv/Scripts/python.exe scripts/audit_premotor.py
```

## Next bounded work

Choose a documented proprioceptive reflex and match its identified afferent and
interneuron types, motor recruitment and muscle targets to these candidates.
Validate the resulting reduced equations against independent response data before
any neural execution. More graph expansion alone would not resolve these gaps.
Then replace the mechanical fixture's arbitrary parameters with supported fly
geometry/actuation and integrate a live viewer. A neural run still requires
explicitly defined telemetry for sustained abnormal activity, feedback mismatch,
rest, blocked effort and any implemented adverse-state dynamics; missing coverage
blocks that run. No test here measures subjective suffering.
