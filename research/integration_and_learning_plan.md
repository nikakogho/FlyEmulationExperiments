# Execution plan and results

## Current revision: spectral input

The user requested explicit UV/blue/green physiology rather than RGB or
grayscale. See `research/spectral_vision.md` for the implemented empirical
spectral front end and executed three-cue neural-memory probes. Those runs
are explicitly exploratory: they do not make the anatomical integration gate
below pass. Biological fidelity and exploratory functional results are now
reported separately. The historical plan and results below are retained.

Objective: improve neural learning in a 3D fly model without a task-solving
controller, and without aversive behavioral experiments. The six-step plan was
executed through its independent component tests and its integration decision.
The integration gate failed on missing functional/anatomical mapping; the
conditional new embodied-learning experiment was therefore not run.

## Plan and actual status

| Step | Work | Result |
|---|---|---|
| 1 | Audit visual inputs to the learning circuit | Complete: missing routes identified and candidate edges exported; integration gate fails |
| 2 | Check 3D retinal transport and timing | Image-axis/permutation/timing checks pass; ten-model recorded-eye replay passes stability checks; world-bearing calibration pending |
| 3 | Test localized plasticity, cue specificity, retention and unpaired/frozen controls | Synthetic mechanism checks pass; fitted biological memory dynamics not established |
| 4 | Integrate only components with justified sensory and modulatory mappings | Held: intermediate-neuron dynamics and compartment assignments not validated |
| 5 | Small non-aversive controlled 3D learning experiment, held-out seeds and cues | Not run because step 4 is not ready |
| 6 | Decide whether results justify further work | Continue anatomical/functional mapping; do not claim improved fly learning yet |

## What the anatomy audit found

The 295 visual KCg-d cells have 39,001 incoming synapses in the supplied
aggregated connectome. Of these, 17,443 originate from neurons omitted by the
current 8,991-neuron subnet. This is an all-input count, not a measured percentage
of sensory information lost. Major omitted input types include aMe12, MTe32,
MTe30, LTe25 and PLP095. No directly presynaptic type matches a FlyVis model
type by exact annotation name. A type-name comparison is not proof that no
biological path exists.

Tracing one additional hop yields **62 candidate intermediate neurons**, with
1,090 upstream and 554 downstream aggregated edges after requiring at least
five synapses per retained edge. Upstream type matches include Tm5a to MTe32
and Tm5b to MTe35. These are real graph connections, not invented direct
T4/T5-to-Kenyon connections. Their identities, positions, transmitter predictions
and both edge sets are exported in `results/visual_learning_path/`.

This is a candidate graph, not a ready calibrated subsystem. FlyVis and the
whole-brain connectome derive from different reconstructions. Type names alone
do not identify equivalent individual neurons or their visual receptive-field
positions. The intermediate neurons' functional parameters are also missing.
The supplied connection table has no synapse coordinates or compartment labels.
Some assignments may be recoverable from additional anatomy/type information,
but they have not been established here.

The literature supports tracing visual projection/interneuron input to visual
KCs, rather than assuming a direct motion-detector input. It also distinguishes
color association from other visual learning tasks.
[Ganguly et al., 2024](https://www.nature.com/articles/s41467-024-49616-z).

## Working recorded-eye interface

`flyplasticity/retinal_bridge.py` preserves 721 receptors per eye and matches
the installed FlyGym RetinaMapper permutation exactly. ID round trips are
exact; horizontal and vertical image gradients retain their axes; the two
eyes remain independent. Black image regions outside receptor masks do not
contribute. Maximum geometric correspondence residual is 0.846 image pixels.

Seventy real eye frames from the prior mechanical rest/walk/rest recording
were resampled to 277 integrator frames by explicit sample-and-hold. Original
acquisition timestamps are retained; this does not invent 200 Hz observations
from a 50 Hz camera. Maximum sample age was 15 ms.

All ten fixed author-listed visual models processed this movie with finite
responses and unchanged neural parameters. No model was selected because it
produced a desired behavior. This validates transport and numerical stability,
not world-bearing calibration, normal spectral responses or learning. The
interface is grayscale; it cannot establish faithful green-versus-blue coding.
No body or whole-brain model ran during replay; isolated visual subsystems did.

## Concrete plasticity change

`flyplasticity/compartment_plasticity.py` is a candidate compartment-local
version of the existing LTD kernel. It requires an explicit mapping of plastic
edges and dopamine neuron groups to compartments; it supplies no default
anatomical assignments. This avoids pooling every dopamine neuron into one
global teaching signal, a limitation of the current pilot. Different biological
compartments have distinct modulatory learning rules, motivating this boundary.
[Aso and Rubin, 2016](https://elifesciences.org/articles/16135).

In a synthetic four-neuron spike-tape fixture, the same active KC has an output
in each of two compartments, while only one compartment's DAN is active:

| Matched-drive comparison | Designated branch weight | Other branch weight |
|---|---:|---:|
| Existing pooled rule | 0.4623 | 0.4623 |
| Candidate local rule | 0.4623 | **1.0000** |

Both started at 1. The unrelated cue's weights remain 1. Frozen weights are
unchanged. With a one-second gap between cue offset and reinforcement onset,
weights remain within 0.00001 of 1. The paired effect remains after 3.5 seconds
of quiet fixture input. The kernel has no long-term forgetting process, so
this is not validation of biological retention over minutes or days.

The initial local test produced a larger update because one active DAN in a
one-neuron group has twice the mean rate of that DAN pooled with an inactive
second neuron. A subsequent **analytically dose-matched diagnostic** halves
local eta and makes the intended-branch update exactly match the pooled case.
The original result is preserved. This isolates locality; it is not evidence
of faster learning. No parameter was optimized against a behavioral score.
These tests use supplied synthetic compartments and arithmetic spike tapes,
not a brain simulation. Locality is guaranteed by the implementation and does
not independently validate the anatomical mapping or receptor dynamics.

## Tests and runnable artifacts

All **42 base-environment unit tests pass**. The earlier dedicated vision-storage
test remains separate. Important commands:

```powershell
.venv/Scripts/python.exe -m unittest discover -s tests -v
.venv/Scripts/python.exe scripts/audit_visual_learning_path.py
.venv/Scripts/python.exe scripts/check_retinal_bridge.py
.venv/Scripts/python.exe scripts/check_compartment_learning.py --matched-drive --out results/compartment_learning_matched
.venv/Scripts/python.exe scripts/check_pipeline_gates.py
```

The final command returns 1 intentionally while anatomical integration remains
unvalidated. Component success and integration failure are separate fields.
Evidence includes `results/pipeline_gates.json`, `results/pipeline_unit_tests.log`,
`results/retinal_bridge/`, `results/retinal_replay/`,
`results/compartment_learning/` and `results/compartment_learning_matched/`.
Audit and component-check scripts use fixed artifact paths; preserve copies
before re-running if keeping separate histories. The replay script refuses to
overwrite its output directory.

## Decision and the next concrete prerequisite

The project remains plausible as a research model, but improved embodied
learning has not been demonstrated. We now have an explicit candidate graph
for the missing route, a checked retinal transport layer, and a local-plasticity
kernel ready for justified compartment assignments. The next prerequisite is
to establish a documented input mapping and functional model for a tractable
subset of those intermediate cells, plus the relevant compartment and output
channel. This can be investigated without running more whole-brain episodes.

We should not spend another cohort's compute testing whether an unvalidated
visual route and pooled output controller happen to reach a light. A future
embodied test must preserve rest, avoid aversive/deprivation mechanisms, use
unpaired and frozen controls, and score held-out preference without passing
goal coordinates into the model. These design constraints do not constitute
a guarantee about subjective experience.
