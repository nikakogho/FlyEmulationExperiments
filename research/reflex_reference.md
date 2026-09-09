# Selected reflex reference and fly-coordinate audit

2026-09-09. Static anatomical and geometric work only. Zero neural steps and zero
physics integration steps. Forward kinematics places the model at supplied joint
coordinates; it does not run a behaving fly.

## Selected biological target

Use the extension-sensitive pathway associated with compensatory tibia flexion
as the first reference. Agrawal et al. report extension-sensitive 13B-alpha
responses and tibia flexion upon activation. This supplies a physiological
directional constraint, not a complete parameterized reflex model.
[Central processing of leg proprioception](https://pubmed.ncbi.nlm.nih.gov/33263281/).

Lee et al. provide subtype-annotated FeCO sensory connectivity in FANC. Their
published data permit separating extension-position claw neurons from movement
and vibration pathways. We downloaded the three relevant CSV tables from commit
4328b1d5549749f1014c4d73cccc0c5241d98ae4 of the author's repository and hashed them.
[Paper](https://www.nature.com/articles/s41467-025-59302-3),
[pinned data](https://github.com/sagrawal/Lee_2024/tree/4328b1d5549749f1014c4d73cccc0c5241d98ae4/synapse_tables).

The extraction finds 613 synapse records from claw-extension cells to annotated
motor neurons (480) or the 13B class (133). These are candidate reference edges:
13B is a broad hemilineage and does not identify 13B-alpha; MN does not specify
which muscle is innervated. We have not matched these FANC cells to MaleCNS IDs.
There is no assertion that all selected edges participate in the selected reflex.

Two postsynaptic IDs have conflicting class annotations. Their raw labels are
preserved in `ambiguous_target_annotations.json` and neither is assigned a class
in the selected pathways. Overall 334 synapse records have unresolved target
classes after this exclusion. We count synapse records, not the CSV's detector
score column. IDs are strings throughout to prevent loss of precision for large
FANC integer identifiers. The test suite exercises this and rejects unresolved
conflicts in the strict lookup function.

## Native fly geometry

The source is the installed FlyGym `neuromechfly_seqik_kinorder_ypr.xml`, recorded
with a SHA256 hash. We used the actual LFFemur, LFTibia and LFTarsus1 body origins
to compute the anatomical interior angle, rather than equating it to qpos.

The 15-position sweep from qpos 0.2 to 1.6 radians gives monotonically decreasing
interior angles: positive qpos means flexion over this interval. At qpos 0.2 the
interior angle is 168.903 degrees. Joint-origin distances are 0.705240 for the
femur and 0.518398 for the tibia in the source model's length units. These are
model segment-origin distances, not independent anatomical measurements.

This establishes coordinate sign and geometry for replacing the previous generic
fixture. It does not calibrate muscle force, activation dynamics, damping or
receptor responses. The generic mechanical fixture is preserved as a software
test, not relabeled as a fly leg. No arbitrary torque is transferred to the
fly geometry. A single neuron-to-single muscle pairing remains unverified.

## Delivered evidence and tests

- `results/reflex_reference/claw_extension_reference_edges.json`: exact FANC IDs
  and per-pair synapse-record counts.
- `results/reflex_reference/joint_coordinate_sweep.json`: native coordinate versus
  anatomical angle and segment-origin distances.
- `results/reflex_reference/report.json`: provenance, uncertainties and execution
  boundaries.
- `results/reflex_reference/unit_tests.log`: all 69 offline tests passed.

Reproduce: `.venv/Scripts/python.exe scripts/reflex_reference.py`.

The next implementation should use the audited anatomical angle convention.
Before closing a neural loop, it still needs a supported cell-level match for
13B-alpha or another identified reflex pathway, motor muscle targets and
physiological response parameters. Merely assigning those properties to cells
with similar names would manufacture the result.

Welfare status: no behaving neural model was instantiated, no aversive or need
mechanism was introduced, and no neural welfare inference was drawn. Existing
requirements for monitored, bounded neural execution remain in force.
