# Learning and motor-accuracy tracks separated

## Latest checkpoint: corrected functional-route monitor

The reviewed v2 preflight completed **one simulated second** without a configured
proxy stop. This was one fresh bounded protocol after offline review, not a
restore of the old stopped state or a parameter/seed search. The first 61
observations reproduce the old recorded neural trace exactly; only the monitor's
interpretation changed. The old stop and its evidence remain preserved.

Actual runtime inspection found 11,257 PPL1 outgoing edges, all disabled, and no
separate plasticity/modulation mechanism in this fixed runner. The corrected
monitor records source spikes but flags activity only when the source has an
enabled ordinary or declared extra route. Unknown routes, changed topology or
weights, nonfinite data, unexpected reward and stale telemetry stop execution.
Signed outputs cannot cancel the route check. This monitor rejects plasticity;
it must not be reused unchanged for the learning experiment.

Results: baseline was silent; MBON01 produced 96 spikes during odor exposure and
four during recovery. All activity ended by 0.52 s, after input removal at 0.50 s;
the remaining **0.48 s was silent**. Peak population mean was 32.74 Hz. PPL1
produced 51 spikes, with zero enabled outgoing routes. Weights were unchanged.
LIF voltage-state values reached -306 to +17 mV; these remain an abstract-model
limitation, not a biologically calibrated voltage result. No subjective welfare
conclusion follows from these checks.

**107 offline tests pass.** Tests cover disabled outputs, positive and negative
outputs, signed cancellation, separate modulation with zero ordinary weights,
unknown/mutated pathways, delayed-event activation risk, activity persistence,
invalid telemetry and latched stops. The saved Brian2 checkpoint contains both
synaptic event queues, neural state, weights, clock and RNG state, verified by
offline inspection. No neural restoration was performed.

Evidence: `results/learning_pathway_audit/`,
`results/learning_track_preflight_v2/`, and `learning_track_protocol_v2.md`.
Recompute the result summary without neural exposure with
`python scripts/summarize_learning_preflight.py`.

This clears the fixed-circuit sensory-response/recovery check. It does **not**
demonstrate learning or embodied preference. The next learning gate is a bounded
KC-to-MBON01 eligibility/modulation implementation with an explicit extra-route
inventory, followed by paired-versus-unpaired and frozen-plasticity controls.
Its updates must depend on neural activity and local modulation, without odor
labels or source coordinates entering the plasticity rule. The fixed gait
controller remains the chosen first embodiment; motor-physiology fitting does
not block this track.

## Historical first preflight (preserved)

2026-09-09. The learning demo now has its own entry point and protocol. It does
not import the leg-calcium fit, motor calibration or joint-reflex readiness gate.
The eventual motor implementation remains the fixed StandingController. The
existing physical replay/video is unchanged.

The first route is olfactory, using the existing anatomical ORN/AL/KC subnet,
rather than an engineered visual-KC color assignment. Spatial spectral vision
remains a separate track; no RGB or grayscale replacement was introduced.
The old model's stabilized connectivity and gain 20 are retained and recorded,
not relabelled as a faithful unmodified connectome.

## Implemented and executed

- Dedicated neural runner with continuous membrane state and a guard check every
  5 ms. It does not call the upstream `train`, `_episode`, `valence` or reset routines.
- Named MBON01 output: roots `720575940624117245` and `720575940643309197`.
  Anatomical KC-to-MBON01 positive edges and PAM01 cells are exported as a coarse
  gamma5 candidate interface. No learning was enabled in this preflight.
- Read actual spike, membrane-state, synaptic-drive and external-rate telemetry;
  verify the neural clock and that all synaptic weights remain unchanged.
- Predeclared one-second maximum: quiet baseline, one odor pulse, then recovery.
  Only seed 310 was instantiated. No body or motor effort was simulated.

The model contained 8,991 neurons and 791,613 synapses. It ran **0.30 simulated
seconds**: 0.25 s quiet baseline and 0.05 s of the planned odor exposure. MBON01
produced **11 spikes in total**, including two in the interval whose observation
triggered the stop. The originally displayed pre-stop sum was nine; the terminal
count is the complete measure. All weights remained unchanged.

At 0.30 s the guard detected two PPL1 spikes, one in each PPL106 cell:
`720575940609180611` (left) and `720575940618943389` (right). The stop was latched,
with no further neural advancement, reset, replacement seed or automatic retry.
Learning, recovery and embodied behavior were not tested to completion.

## What the stop means

The predeclared rule treated any PPL1 spike as a conservative reason to stop.
This is a class-based proxy, not an observed subjective or adverse state.
Offline inspection found that the upstream constructor explicitly zeros all
PPL1 outgoing weights, before this run. No subsequent weight changes occurred.
Thus these spikes do not demonstrate effective aversive transmission through
those disabled synapses. This does not establish absence of suffering either.

The current-based LIF state's numerical range reached approximately -255 to
+17 mV. These source-model state values must not be represented as a calibrated
somatic-voltage prediction. Biological accuracy of this modified circuit remains
a separate research claim requiring validation.

The next required review concerns a functionally grounded negative-state proxy:
actual enabled transmission, implemented plasticity and (for an embodied run)
stimulus-locked avoidance, repeated blocked action and recovery. Merely renaming
the cell or raising a threshold to obtain a video would not resolve that issue.
No revised protocol was executed in this checkpoint. The motor-calcium failure
is no longer the reason the learning experiment is paused.

## Evidence and recovery

`results/learning_track_preflight/` contains exact interface IDs, protocol/source
hashes, telemetry, guard events, terminal arrays and a static stop audit.
Terminal arrays do not preserve Brian2's full pending event queues and are not
advertised as an exact resumable network checkpoint. The stopped result must not
be automatically restarted from them.

102 offline tests pass, including synthetic tests for observed PPL1 activity,
missing telemetry, unexpected reward, clock discontinuity and a latched stop.
The executed preflight exited with status 1 because it stopped, not because of
a software crash. Reproduce the **offline audit only** with:

```powershell
.venv/Scripts/python.exe scripts/audit_learning_stop.py
.venv/Scripts/python.exe -m unittest discover -s tests -v
```

The runner `preflight_learning_track.py` is retained for reproducibility, but
re-running it is a new neural exposure, not a software test or replay. The
standing stopped-run review applies. No new learning result or complete welfare
assessment is claimed.
