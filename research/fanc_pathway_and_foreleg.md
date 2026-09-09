# Within-FANC pathway and anatomical foreleg: steps 1 and 2

2026-09-09. Both requested component deliverables are implemented. This does not
establish physiological reflex dynamics, muscle force calibration or learning.

## Step 1: exact sensory-to-muscle identity chain

The preceding scene-based motor pool was too broad to identify a muscle. We now
use the author's motor connectivity matrix, whose column metadata explicitly
contains side, nerve, segment, function, muscle, rank and FANC segment ID.
The source is pinned to Lesser/Azevedo commit
93cafa55b8bbdb1493e8d73c941035969349b223, file
`pkls/pre_to_mn_df_matched_typed_with_nt_v604_20230525.pkl`.

Joining exact IDs to the Lee et al. claw-extension annotations establishes a
direct anatomical route from five position-sensitive cells to motor cell
**648518346496932836**, labeled **main_tibia_flexor**, left side.

| Sensory cell, FANC ID | Recorded synapses onto that motor cell |
|---|---:|
| 648518346481759933 | 5 |
| 648518346487912272 | 12 |
| 648518346488815453 | 17 |
| 648518346503978080 | 10 |
| 648518346508752447 | 14 |
| Total | 58 |

No cell identities or edges were transferred between specimens. This is an
anatomical pathway, not a closed six-neuron nervous system: other inputs and
motor units are omitted. Single-cell tuning, synaptic efficacy, recruitment and
force per spike remain unmeasured here. We do not infer a functional reflex from
synapse counts alone. Other reference records that did not match the older motor
metadata remain unmatched (347 contacts); they are not guessed from nearby IDs.

The saved pickle is read with an explicit class allowlist, with one compatibility
mapping for pandas Int64Index. The exporter preserves integer identifiers as
strings and rejects ambiguous target records. The derived mapping, source hash
and limits are in `results/fanc_exact_pathway/`.

Sources: [motor matrix](https://github.com/tuthill-lab/Lesser_Azevedo_2023/blob/93cafa55b8bbdb1493e8d73c941035969349b223/pkls/pre_to_mn_df_matched_typed_with_nt_v604_20230525.pkl),
[sensory tables](https://github.com/sagrawal/Lee_2024/tree/4328b1d5549749f1014c4d73cccc0c5241d98ae4/synapse_tables).

## Step 2: anatomical mechanical foreleg

The new rig extracts the actual left-front leg from installed FlyGym geometry,
preserving its meshes, masses, joint axis, local poses and tibia damping. It
immobilizes the other joints at their source reference pose, mounts the coxa at
the origin, disables gravity and ground contact, and permits only the tibia hinge
to move. This is a supported mechanical preparation, not a freely behaving fly.

Two filtered opposing torque actuators provide explicit engineering inputs of up
to 0.006 source torque units. These are not Hill muscles or calibrated motor-unit
forces. The 0.2–1.6 rad coordinate limit is the selected test interval, not a
measured anatomical range limit. Geometry is improved; biological force fidelity
is not yet established. Source XML and hash accompany the generated model.

The run demonstrates flexion, extension and passive settling. Source stiffness
is zero, so the joint stops through damping rather than returning to a preferred
angle. This removes the earlier generic fixture's artificial spring assumption.
The viewer reports anatomical angle explicitly. The rendered trajectory matches
an unrendered reference exactly, and the final velocity is approximately zero.

Video: `results/fly_leg_framed/foreleg.mp4` (85 decoded frames). The full-leg camera
was visually checked. JSON telemetry, stop events, report and editable MJCF model
are saved in that directory. The original closer-camera render is preserved.

## Tests and welfare boundary

All 75 offline tests pass, including the new exact-ID/unknown-target tests,
anatomical actuation direction, passive settling, neural-attachment rejection
and latched fault-stop behavior. Each mechanical run performs 2,400 physics steps.
An injected telemetry fault prevents the next physics step; there is no automatic
restart. Re-rendering used a separate mechanical-only instance.

No neural circuit, aversive input, valence variable or modeled need was introduced.
No claims about neural welfare or absence of suffering follow from these results.
The anatomical pathway is not connected to the rig. A future neural run still
requires calibrated sensory/motor dynamics and actual welfare-proxy coverage.

Reproduce with fresh output:

```powershell
.venv/Scripts/python.exe scripts/fanc_exact_pathway.py
.venv/Scripts/python.exe scripts/run_fly_leg.py --out results/fly_leg_repeat
.venv/Scripts/python.exe -m unittest discover -s tests -v
```
