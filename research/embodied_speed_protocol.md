# Bounded conditioned-locomotion test — 2026-09-10

Independent learning validation passed (four-case mean S=.22017, all paired
advantages positive). The six-assay lateral MBON test failed. This protocol
does NOT waive the direction gate or claim learned source navigation. It tests
a narrower scalar motor effect in a real continuously coupled 3D physics scene.
The user's authorization covers the fixed engineering gait and bounded controls.

Exactly six runs: test odor A then B, each with paired, unpaired and frozen
memory from validation seed311_A. This case was specified here as the first
validation case, not selected for best performance. Two seconds of neural/physics
coupling per run, twelve seconds maximum. Any stop cancels remaining runs.

Construct/settle the physical body for .30 s with no brain present. Then construct
the identical subnet and restore its full successfully completed validation
checkpoint (clock, RNG, pending events and state), not just weights. Neural time
is relative to that terminal checkpoint. Existing completed memories are used
for prospectively specified comparison runs; stopped states are never retried.
No plasticity or reinforcement during this test, no aversive stimuli or needs.

One Gaussian source at (6,0,1) mm, sigma6mm, carrying only the test odor; a purely
visual marker indicates its position. The source apparatus is off 0–.25s, on
.25–1.20s, off thereafter. Actual body antenna/palp positions drive the sampled
field. Known ORN side/nerve labels route concentrations; unknown side explicitly
uses bilateral mean. These fields/rates are engineering approximations. No
visual RGB input, stimulus coordinate or cue label reaches the motor readout.

Read mean MBON01 firing with a fixed100ms exponential filter. Equal left/right
gait command = .35 + .35*clip(filtered_rate/160Hz,0,1). This is a transparent
engineering transfer function, not identified fly motor physiology. No turning
or source-following rule exists. Request rest until .35s and after1.20s. The
constants are declared before exposure and are not tuned on the trajectories.

Before each5ms block inspect full fixed-pathway/neural telemetry as in preflight,
actual input rates/clock, and measured body position, command and odor. Neural
and physics clocks must match elapsed time. Body physics uses50 steps of .1ms.
Check each physical substep for finite state and termination. Stop for any
BehaviorMonitor proxy (blocked effort, failed rest, competing commands, or
stimulus-linked concentration decline). These proxies have known false-positive
risk (the scripted mechanical pass-by triggered one); they remain conservative
investigation stops here. No suppression of an in-run stop or corrective stimuli.
The avoidance comparison requires an uninterrupted enabled stimulus window;
experimenter-controlled source removal is explicitly observed and is not
misclassified as the body moving away. Other movement/rest proxies stay active.

At2s require last50ms neural quiet and physical speed<.5mm/s. Retain all neural
and body states/telemetry/video, including stops. There is no claim of subjective
welfare or complete sensory coverage. This is an olfactory-subnet hybrid.

Primary motor outcome: median measured horizontal velocity during .65–1.15s.
Require paired-A slower than both unpaired-A and frozen-A by>=5%, and the
A-specific fractional slowing relative to frozen exceeding B-specific slowing
by>=5 percentage points. All runs must complete with recovery. Report distance
and actual rates too. This is an exploratory engineering effect test, not a
population test. A pass supports memory-dependent slowing only, never learned
navigation. No extra cases or parameter changes after the result.

The navigation limitation is consistent with the existence of additional
learned-valence-to-movement pathways:
[Neural circuit mechanisms for transforming learned olfactory valences into
wind-oriented movement](https://elifesciences.org/articles/85756).
