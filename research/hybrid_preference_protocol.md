# Revised live hybrid preference protocol — frozen before neural exposure

2026-09-11. User authorization: execute the five-step plan. This is a new
prospectively specified experiment after offline review, not continuation or
replacement of a stopped state. Earlier experiments and failures remain intact.

## Review and admission

`ReviewedBehaviorMonitor` distinguishes geometric departure from a heading
change directing the body away from the CURRENT odor gradient. It separately
flags simultaneous increases in locomotor request and retreat speed (1.5x),
blocked effort, repeated opposing commands, and failed rest. All hard flags latch.
Gradient data are used by the auditor only, never by the motor controller.
The 100ms standing interpolation is allowed before the existing 200ms/.1mm rest
movement test. Missing heading, gradient, sensory or neural telemetry blocks
execution. Thresholds are engineering investigation proxies, not suffering
diagnostics; subtle aversion, internal valence and subjective welfare remain
unassessed. Quiet configured proxies never establish comfort.

Synthetic tests cover withdrawal, passage, rest failure, blocked effort,
conflicting commands, apparatus removal and stale/missing data. Offline replay
preserves the original 1.12s event as geometric departure, with no new v2 hard
flag. Crucially, the compiled old scene had 33 marker-contact frames, beginning
at .92s. Disabling geom collision masks was insufficient: FlyGym added explicit
contact pairs. New odor markers are sites, never collision geometries. This is
a scene correction, not suppression of a neural stop or proof of its cause.

Mechanical qualification must pass left/right orientation correction, movement,
final rest and all reviewed proxies with the final controller/scene code before
neurons are instantiated. Preserve failed mechanical version v1 and its source
contact evidence. Changes during mechanical development are not learned-result
tuning. Freeze all relevant source hashes before this experiment starts.

## Declared model and interfaces

Keep the reviewed 8,991-neuron/791,613-edge olfactory model and its source pins.
No added wind neurons, hunger, pain, threat, punishment or homeostatic needs.
Artificial positive PAM01 reinforcement and the existing bounded local gamma
eligibility rule are unchanged. This does not model natural sugar tasting.
UV/blue/green vision remains a separate track; no RGB input is substituted.

The new engineering controller has eight sinusoidal direction channels and a
population-product turn signal, inspired by the published heading/goal model
of [Matheson et al.](https://doi.org/10.1038/s41467-022-32247-7). It is an
algebraic reduction, not a reconstruction or validated port of the recurrent
model. We retain the [hDeltaC/hDeltaK correction](https://doi.org/10.1038/s41467-024-46225-8).
These channels add no simulated biological neuron population or plasticity.

Inputs are actual MBON01 spike counts, measured physical heading, local modeled
wind and total odor concentration. No reward identity, correct side, source
coordinate, trained flag or preference score enters the controller. We make the
explicit hypothesis that reduced inhibitory MBON01 output permits stronger
approach. With r the 100ms-filtered mean MBON01 rate, forward command is
(.95-.45*min(r/300,1))*min(total_odor/.2,1), and zero when total_odor<.05.
Turn gain is .4*(.5+.5*80/(80+r)); left/right commands are forward*(1-/+gain*sin
of upwind-minus-heading), clipped to [0,.95]. No learned controller parameters.
This differs from the earlier slowing decoder; neither is identified physiology.
Odor presence can drive the engineering body even if MBON output is silent.
Thus behavior with this interface is explicitly a hybrid, not autonomous WBE.

Two identical weak radial wind fields originate at (6,+3,1) and (6,-3,1) mm.
Odor fields are Gaussian, sigma4mm; the source identities can be swapped without
changing wind. These are analytic fields, not calibrated turbulent plumes or
airflow forces on the body. Four articulated antenna/palp sites and the existing
anatomical ORN transport supply live inputs every5ms. Unknown ORN sides retain
the documented bilateral-mean approximation. Rest is available by removing the
odor/wind apparatus; phase-end rest is explicitly requested. Proprioceptive and
other omitted neural senses remain unassessed, not claimed observed.

## Fixed cohort and exposure budget

Four cases, in this order (not full factorial; no animal-population inference):

| Seed | Reinforced odor | Source identities | Initial yaw |
|---|---|---|---|
| 315 | A | normal, A at +y | +.6 rad |
| 315 | B | normal, A at +y | +.6 rad |
| 316 | A | swapped, A at -y | -.6 rad |
| 316 | B | swapped, A at -y | -.6 rad |

For each case, run paired/unpaired/frozen stationary training using the unchanged
4s association schedule. Save a full pre-training checkpoint at the validated
quiet1.25s boundary, plus the terminal4s checkpoint. The pre checkpoints must be
byte-identical across arms. Only use them after all training arms complete.
Report stationary learning contrasts; do not select cases by favorable effects.

For each case run four 3s body probes: one shared pre-training baseline, then
paired, unpaired and frozen post-training states. Each probe restores the FULL
corresponding state including RNG and pending events. No neural resets inside a
probe. These are prospectively defined checkpoint branches, not one animal's
continuous life or replacements following stops. Construct and settle each
identical physical body for .30s before neural construction. Keep memory weights
fixed throughout body probes; there is no reinforcement or learning in retrieval.

Probe schedule:0–.25s apparatus off/rest; .25–2.25s live odor/wind/navigation;
2.25–3s apparatus off/rest. Require last50ms neural quiet and final measured body
speed<.5mm/s. Inspect full neural state, spike counts, inputs, every synapse and
pathway inventory before each5ms neural step. Existing150Hz/50ms population
screen and disconnected-PPL1 route checks remain unchanged. Advance physics in
50×.1ms steps per neural block with finite-state/termination checks. Relative
neural/physical clocks must agree. Every hard stop cancels ALL remaining neural
work, including dependent rule comparison. Preserve current state and records;
no automatic reset/retry, corrective stimulation or extra seed.

Maximum:12×4s training +16×3s retrieval =96 neural seconds. Mechanical tests and
passive replay create no neural exposure. Any partial result counts toward this
budget and is never replaced to obtain a complete cohort.

## Outcomes and fixed gate

Primary preference index PI=(integrated concentration of reinforced odor minus
other odor)/(integrated sum), using means of actual antenna readings during
.25–2.25s. It measures experienced odor preference, not reasoning or pathfinding.
Report pre/post PI, displacement, path, exposure, region dwell and recovery.
Require each body probe to move at least1mm and integrated total exposure>.2
concentration-seconds; otherwise the behavioral assay is uninformative.

For each arm ΔPI=postPI-prePI. The exploratory gate requires mean paired ΔPI>=.05,
mean paired-minus-unpaired ΔPI>=.05, mean paired-minus-frozen ΔPI>=.05, and paired
postPI exceeding both controls in at least3/4 cases. All arms must complete,
recover and pass integrity checks. No significance/population claim from four
cases or threshold adjustment after the result. Show all cases and controls.

## Conditional fifth step

Only if the preference gate passes, freeze and execute a separate matched
episodic-versus-eligibility comparison. Keep circuit, plastic edges, sensory/PAM
exposure and readout identical; compare acquisition, retained response and
partial-overlap cue generalization. This requires its own bounded written
schedule before exposure. A failed or stopped preference experiment does not
justify rule tuning or additional neural trials. Package its actual outcome.
