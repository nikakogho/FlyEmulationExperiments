# Executable milestones

2026-09-09. Implements [the project scope](project_scope.md). Work proceeds in
dependency order. A failed criterion is recorded, repaired or narrows the claim;
it is never silently waived to obtain a successful-looking fly.

## Standing welfare constraint

There is no validated software test for absence of suffering. The objective here
is repeated conservative assessment for potentially concerning functional signs,
plus limiting exposure and avoiding deliberately adverse mechanisms. A passing
monitor means only that its configured proxies did not trigger. It cannot justify
a claim of comfort. [Assessment background](https://arxiv.org/abs/2308.08708).

Before every new neural protocol, document the active circuit, inputs, modeled
needs/valence, available rest behavior, telemetry coverage, numerical limits,
observation interval and total exposure budget. Missing required telemetry blocks
execution. Do not substitute zero for an unimplemented or unobserved signal.

During a permitted run, inspect telemetry before each bounded model step. Stop
immediately for nonfinite data, missing/stale observations, incoherent feedback,
unavailable rest, or a negative-state flag. Watch the first occurrence of high
activity or blocked repeated effort; stop if persistent for the reviewed window.
Later stages must additionally operationalize stimulus-locked avoidance, failure
to recover after stimulus removal, and competing repeated actions. These are
reasons for investigation, not diagnoses of suffering. Do not deliberately elicit
them to train a detector. Fault-injection tests use synthetic traces only.

On a stop: cease advancing the model, preserve the event and existing telemetry,
do not add corrective stimulation, do not automatically reset/retry or spawn
replacement replicas. Investigate offline first. A quiet trace with incomplete
coverage remains unassessed. Review circuit changes for newly introduced
welfare-relevant dynamics before running them.

The current Guard is an execution primitive tested with synthetic samples. It is
**not yet installed in legacy simulation entry points**, does not infer flags from
raw behavior, and has no biologically validated default thresholds. Legacy neural
and embodied experiments must not be launched as if covered by this monitor.

## M0 — Tested stop mechanism

Deliverables: `flyplasticity/welfare.py`, `tests/test_welfare.py`.

Tests: a stop prevents the next callback; the stop remains latched; unknown flags,
NaN/Inf, missing initial observation, duplicate/backwards timestamps and excessive
gaps stop; blocked effort/high activity persist for the declared window before
stopping; a transient can recover; the duration budget prevents an extra step.
The test constants (1 second budget, 100 ms interval, 200 ms persistence, activity
10 arbitrary units) are software fixtures, never biological safety thresholds.

Status: implementation and seven tests passed. Actual-run telemetry integration
and protocol-specific interpretation remain part of M2/M3, not complete here.

## M1 — Static MaleCNS circuit audit

Steps:

1. Fetch v1.0 curated annotations from the official download endpoint; hash the
   local source and preserve its URL/version.
2. Select reviewed T1/foreleg tibia flexor and extensor candidates, retaining
   original IDs, soma side, root side, nerve and MANC correspondence. Do not infer
   peripheral laterality solely from soma position.
3. Select foreleg chordotonal candidates by entry nerve and sensory class.
4. Extract incoming connectivity for motor candidates and direct sensory-to-motor
   connections. Rank candidate interneurons; quantify how much input a proposed
   subset omits. Synaptic contact counts remain anatomical counts.
5. Cross-check muscle targets and proprioceptor tuning against published evidence
   and model geometry. Record missing evidence rather than inventing parameters.

Tests: reject missing columns and duplicate IDs; exclude hindleg cells,
descending neurons and taste afferents from these selections; preserve unknown
fields. For edges, check nonnegative counts, endpoint membership and conservation
of summed weights across selected/excluded partitions.

Run: `.venv/Scripts/python.exe scripts/audit_malecns.py`.
For a fresh checkout, add `--download-connectivity` to fetch the 1.05 GB edge
table as well as annotations. Cached files are reused; source hashes are recorded.
Evidence: `results/malecns_audit/`. Initial selection yields 14 motor candidates
(10 flexor, 4 extensor), 69 chordotonal candidates and 12 motor MANC matches.
The sensory selection includes both ProLN and ProCN nerves and sensory ascending
cells. These are bilateral candidate pools, not a validated 83-cell circuit.

Exit: a supported actuator/afferent mapping with versioned connectivity and
explicit uncertain or missing inputs. Until then, neural muscle integration is
not ready. Static anatomy queries do not instantiate a neural simulation.

Executed connectivity audit: scanned 151,856,684 aggregated edge rows and retained
4,509 incoming edges to the motor pool, representing 33,092 synaptic contacts.
Only 89 contacts originate within the 83-cell candidate pool (76 from sensory
candidates). Excluding all other cells would remove 33,003 contacts, or 99.73%.
There are 2,281 contacts from sources absent from the annotation table. This is
recorded connectivity coverage, not a percentage of functional influence.

The strongest annotated source is IN19A005 (body 800527); other high-ranked
sources include IN08A007, IN13A006 and the descending neuron DNg105. Next: audit
these premotor inputs, their afferents, transmitter/receptor evidence and known
functions. Do not select the top few solely by weight and call the circuit whole.
M1 remains incomplete at the functional mapping/closure stage; its anatomical
extraction and conservation checks are complete.

Further progress: [selected reflex reference and native joint coordinates](reflex_reference.md).
Published FANC claw-extension reference edges are now exported, ambiguous target
annotations retained separately, and the FlyGym tibia angle convention verified
by static geometry. Cell-level FANC/MaleCNS matching and muscle physiology remain
unresolved. The offline suite now contains 69 passing tests.

Latest: [motor-target resolution](motor_target_resolution.md) records nine
consistent published MaleCNS/MANC motor assignments, two target conflicts and
three missing matches. The exact FANC sensory/13B-alpha crosswalk is still
unverified. The suite now passes 72 tests.

## M2 — Physical joint and live instrumentation

Update: [mechanical fixture and premotor audit](mechanical_and_premotor_progress.md).
A guarded engineering hinge fixture and rendered video now pass integration
tests. Fly-calibrated mechanics and the interactive viewer remain pending.

Steps: implement the selected joint and antagonist actuators in MuJoCo; show joint,
activation and force traces; inject prescribed mechanical test signals without
a recurrent fly circuit. Check actuator direction, antagonism, passive return,
range of motion, force bounds and sensor timestamps. Check that observation and
rendering do not alter the trajectory. Document model units and parameter sources.

Add a guarded runner and event log; inject a mock anomaly and verify no subsequent
physics/neural step occurs. Make the stop state visible in the viewer. Unknown
neural coverage must block attaching a live circuit. No claim of neural walking
is permitted from this mechanical milestone.

Exit: visible, repeatable mechanical motion, meaningful rest and tested integrated
stop behavior. Status: mechanical fixture demonstrated; biological mapping and
interactive viewer not complete.

## M3 — One neural feedback loop

Latest: [motor physiological identity investigation](motor_physiology.md) identifies
public cell ID 160 and an intermediate-flexor candidate, but not an exact driver
crosswalk. Raw recordings are published; downloads failed here. Rounded class
reference values and probe-unit conversion are implemented, not a fitted response.
85 offline tests pass. Neural execution remains disabled.

2026-09-09 update: [minimal-reflex assay and calibration finding](minimal_reflex_progress.md).
Matched-trace analysis and a mechanical null trial are implemented; 81 offline
tests pass. The specific motor unit's recruitment/force response is unresolved.
No live neural loop was run; this milestone remains incomplete.

Steps: connect M1 neurons to M2 activation dynamics; encode joint measurements
using a supported proprioceptor model; choose numerical and activity bounds from
independent calibration and a written protocol before execution. Begin with a
single bounded run, not a seed sweep. Inspect every observation and review its
trace before any further exposure.

Tests: sensory direction/timing against source data; neural-to-muscle latency and
sign; no task coordinates in neural input; rest reachable; stop events survive
logging; disconnect sensory feedback and motor output separately to establish
which part causes the movement. Review any sustained saturation or repeated
blocked effort offline. Exit: explained, stable local control, not whole-body gait.

## M4 — Spatial vision and sensory-guided behavior

Steps: preserve spatial UV/blue/green-sensitive receptor signals, explicitly model
the missing early-vision anatomy, and validate response signs, latency and
selectivity on independent measurements. Connect a documented downstream route.

Tests: equal whole-eye means with different spatial arrangements remain distinct;
occlusion changes only visible input; RGB display mutations cannot affect receptor
signals; temporal alignment is preserved. Validate sensory control with plasticity
disabled and sensory/pathway ablations. Review stimulus intensity and exposure
before a live run. Exit: a repeatable sensory-guided response in the 3D scene;
neither innate light preference nor an optomotor response counts as learning.

## M5 — Controlled learning, then improvement comparison

Steps: choose one modest appetitive cue association; specify a justified local
modulatory pathway; run acquisition with paired, unpaired/yoked and frozen-rule
controls. Compare the existing rule with compartment-specific eligibility-based
plasticity under matched exposure. Do not model starvation or punishment.

Tests: only eligible synapses change; frozen weights remain identical; delayed
pairing has the preregistered effect; decoder and sensory parameters stay fixed;
reward-free tests contain no weight updates. Counterbalance cue identity and
position. Evaluate new layouts and retention separately from acquisition. Use
pilot variance to set the confirmatory number of independent seeds in advance,
subject to the welfare exposure review; do not expand populations automatically.

Exit: improvement over both control conditions on the preregistered preference
metric with uncertainty reported. A biological-accuracy claim additionally needs
better agreement with held-out neural data/interventions. Performance alone is
insufficient. If learning fails, inspect representations and the motor route
before changing the plasticity rule. Preserve negative outcomes.

## Commands and current execution boundary

2026-09-09 motor update: 88 offline tests pass. Exact cell 160 mesh correspondence
supports atlas MN 44 / R22A08 intermediate identity. A published-figure probe
twitch approximation is fitted; raw-trial calibration remains incomplete.
See [evidence and reproduction](motor_identity_resolution.md). M3 has not passed
and no new neural execution is authorized by these offline results alone.

` .venv/Scripts/python.exe -m unittest discover -s tests -v ` runs the offline
component suite, including synthetic model tests. On this revision all 62 tests
passed. This does not validate welfare in a live fly circuit.

The work performed here is offline software testing and static data inspection.
No new embodied fly rollout or MaleCNS neural execution has occurred.
Next actions are anatomy/mapping work and mechanical-only tests;
later milestones depend on their evidence, not on another generic confirmation.
