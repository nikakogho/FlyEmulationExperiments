# Follow-through review, 2026-09-11

## Execution boundary

The user authorized steps 1–7 through resolvable issues. This review uses saved
traces, synthetic tests, static anatomy and mechanical bodies only. It does not
resume the stopped neural state, construct replacement neural trials, relax the
active behavioral monitor, or infer comfort. The stopped six-arm experiment
remains stopped with five cancelled controls.

## 1. Behavioral stop

The configured event is a concentration-rise/fall plus movement heuristic. It
does not require a change of heading, acceleration, or motor choice after a cue.
Consequently a constant-command straight pass through a static odor field can
trigger it. The existing synthetic test itself has constant commands and a
straight trajectory. That is evidence of a specificity limitation, not an
avoidance ground truth. The independently scripted mechanical replay also
triggered it. Preserve both events and the original monitor unchanged.

The next detector needs separate channels for stimulus departure and observed
withdrawal actions, and evidence linking the latter to the stimulus. With only
one stopped neural trial, no matched counterfactual, and no observed recovery,
we cannot resolve stimulus-caused acceleration versus other speed variation.
Equal left/right commands alone do not establish absence of avoidance.

## 2–3. Value, direction and anatomy

Primary paper: [Aso et al. 2023](https://elifesciences.org/articles/85756).
Reproducible full-text input:
https://cdn.elifesciences.org/articles/85756/elife-85756-v3.xml (local ignored
`data/elife85756.xml`; downloaded successfully after the article XML endpoint
returned HTTP 403).

The paper distinguishes memory compartments: gamma5/beta-prime2a conditioning
did not significantly promote upwind displacement in that assay, unlike alpha1
and beta1/beta2. Its UpWiN population receives MBON-alpha1/alpha3 input and has
heterogeneous membership. SMP108 activation affected movement, but blocking it
did not impair appetitive memory retrieval. The authors also discuss routes
through FB6D/6I/6T and hDelta cells, and wind input via aristae/Johnston's organ.
Thus MBON01-to-SMP108 is not a sufficient recipe for learned steering.

`scripts/trace_navigation_paths.py` checks the full 15,091,983-row table, verifies
root IDs against index order, exports directed shortest-path witnesses with
actual contacts, and audits input closure. Routes exist; absence of a direct
edge is not absence of any path. Witnesses are neither strength ranked nor
physiologically validated. Exact SMP354 is absent from this annotation table;
similar names must not silently replace it. The selected 73 cells retain 3,676
of 182,181 incoming contacts (2.02%). This is an anatomical coverage warning,
not a universal requirement to simulate every upstream neuron.

Resolved correspondence: the cached official MaleCNS annotation explicitly maps
SMP354 to FlyWire types CB3112 and SMP355. The current FlyWire table contains six
CB3112 cells and no exact SMP355. They receive MBON07/14 input and project to
SMP108/FB6D/FB6I. The report retains the MaleCNS rows and their rough/preliminary
tracing labels. This is a type cross-reference, not identity between specimens.
With those six candidates the pool retains 4,508/183,712 contacts (2.45%).

We also inspected the authors' [published navigation model](https://github.com/nagellab/Mathesonetal2022/tree/30bc47c0703527995af2a9d671bd2a1f32c1a29a/Model%20Code),
pinning source hashes in `results/navigation_model_sources.json`. It accepts
wind/heading angles, synthesizes neural population inputs, uses an eight-column
inhibition model, and explicitly converts output into heading and speed. It has
no calibrated interface for our MBON01 memory. Using it would be a transparent
reduced-model extension, not spontaneous navigation of the existing connectome.

Crucially, the [2024 addendum](https://doi.org/10.1038/s41467-024-46225-8)
reassigns the interpretation of a key driver: VT062617 additionally or
predominantly labels hDeltaK, so the original hDeltaC sensory/behavioral effects
may belong to hDeltaK. Their direct inputs differ. We retrieved and checked the
full addendum, rather than treating the original functional mapping as settled.

## 4. Candidate-circuit readiness

Stationary neural testing is not ready: no supported wind-to-cell encoding or
calibrated directional readout is implemented. SMP354 name correspondence is
resolved to candidate types; the hDelta functional assignment remains qualified.
Finding short paths does not supply their missing dynamics. The candidate
SMP108/PAM feedback also requires a new review before enabling additional
reinforcement routes. No new neural candidate assay is authorized by this file.

## 5. Independent mechanical diagnostic

We can still test whether archived learning-associated outputs can affect the
engineering body. Decode all twelve completed stationary validation traces with
the unchanged NeuralSpeed filter, preserving the full filter history. Saved
total MBON01 counts are sufficient for its mean-only input; assigning the sum
to one array slot is algebraic and makes no laterality claim.

For mechanical comparison, use the first previously declared case seed311_A,
both odors and all three arms. Each body uses identical seed101/setup, settles
for .30s without neurons, executes exactly the 50 archived post-probe commands
at 5ms each, and then receives zero command for .50s. No stretching, repetition,
parameter search or source-following control. There are no neural processes,
needs, rewards, sensory feedback to neurons, or neural resets in this diagnostic.
Preserve every result. Report displacement, mean measured probe speed, final
rest speed and finite-state completion; do not apply the stopped experiment's
different duration/window or claim that its behavioral learning gate passed.

## 6–7. Delivery scope

Package the controlled mechanical playback with an explicit on-video label:
archived neural outputs, no live brain or feedback. It can demonstrate that the
fixed body interface expresses differences in saved traces. The previous stopped
closed-loop video remains separate. Neither is learned source navigation.

The remaining live-navigation blocker is a supported functional interface plus
adequate behavioral interpretation/recovery coverage. No missing user download
or extra GPU computation resolves those scientific choices automatically.

## Results

All six mechanical trials completed. The independent archive audit verifies
identical starting qpos/qvel/act, unmodified commands, finite states, aligned
timestamps and final rest. Measured mean speed during the 250ms probes:

| Archived response | Paired | Unpaired | Frozen |
|---|---:|---:|---:|
| Odor A | 8.261 mm/s | 9.076 mm/s | 9.399 mm/s |
| Odor B | 9.784 mm/s | 10.017 mm/s | 9.668 mm/s |

For A, paired playback was 8.97% slower than unpaired and 12.11% slower than
frozen. For B, it was 2.32% slower than unpaired and 1.20% faster than frozen.
These are deterministic mechanical comparisons of one archived training case,
not independent animal/seed replication or closed-loop learning. They establish
a working memory-output-to-body interface under the stated engineering mapping.
The original embodied experiment remains stopped; its gate has not passed.

Current step status: 1 offline explanation and negative-control test complete,
but neural-event causality/recovery remains unresolved; 2 value/direction
separation complete; 3 expanded anatomical audit and correspondence complete,
functional closure incomplete; 4 blocked on that functional specification;
5 mechanical playback comparison complete, live controlled test incomplete;
6 learned navigation blocked; 7 honest comparison video delivered, final live
learning/navigation deliverable incomplete. No new neural exposure was made.
