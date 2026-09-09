# Exploratory light-cue conditioning: fixed pilot protocol

This is a separate hypothesis pilot, not promotion of the unresolved Huang
reproduction. It tests actual connectome-derived activity in the MuJoCo garden.

## Declared abstractions

The circuit retains Daniel's 8,991 neurons, stabilization edits and gain 20.
The 295 annotated KCg-d cells receive synthetic green/blue selectivity, balanced
within each hemisphere using the experiment seed. A fixed color-opponent pixel
feature from FlyGym's two rendered eye cameras drives those cells through
Poisson input. Geometry occlusion is supplied by the renderer. There is no
reconstructed optic-lobe transformation or calibrated spectral sensitivity.

The 2,806 existing visual-KC to MBON edges receive local temporal LTD (10 ms
updates, 100 ms KC eligibility, 50 ms pooled PAM trace, eta 4/s), extending the
previous exploratory rule to visual KCs. No compartments, LTP or calibrated
receptor dynamics are claimed. The baseline circuit can activate PAMs even
without external reinforcement; measure changes in the absence of food.

The food-contact proxy is body XY distance <=2.5 mm from the green cue's floor
patch, with body Z<2.5 mm. This triggers an engineered 60 Hz PAM input. It is a
local contact-volume approximation, not a recovered gustatory pathway. No
gradient reward is supplied. Taste reaches the plasticity rule only via spikes.

The controller receives two hemispheric mean MBON firing rates and seeded,
color-blind exploration noise. Differential avoidance maps to a fixed reflex
walking controller. No source coordinates, cue labels, routes or success flags
enter the neural model or controller. Source coordinates are used only for
placing the scene, the local contact sensor, and evaluation.

## Acquisition and evaluation

Seeds 0,1,2. Conditions: plasticity enabled, frozen weights, and temporally
shifted reward replay. Each receives three acquisition episodes of 2.4 seconds,
resetting the body to the start with headings -0.35,0,+0.35 radians. Neural state
and weights persist across acquisition resets; these are experimental resets,
not successful-route demonstrations. Acquisition cue positions are counterbalanced
by seed. No conditioning is supplied before acquisition.

The shifted-reward control replays each plastic condition's reward trace shifted
by 1.2 seconds, without physical food. This preserves reward count but does not
guarantee independence when visual cues persist. Report this limitation and
measure cue-reward overlap. Do not label it a perfectly unpaired control.

After acquisition, save weights. Run food-free, learning-disabled tests for 2.4
seconds at both cue arrangements from the same body start and heading. Reset
neural dynamical state to the same initial snapshot while retaining each
condition's weights. No coordinate-based stopping. Seed 0 videos are selected
before outcomes are inspected, including failures.

Primary descriptive outcome: fraction of test decisions within 3 mm of green
minus fraction within 3 mm of blue, averaged across original/swapped layouts.
Also report visits, final/closest distances, acquisition contact count, visual
input, spikes and weight changes. Report all failed physical runs, not only
successes. Three seeds are a pilot, not a powered biological comparison. If no
food is encountered, no conclusion about reward association is justified. If
preference does not exceed frozen and shifted controls, do not claim learning.

The 0.5 ms physics timestep is subject to a separate body-only preflight before
acquisition. If unstable, use the prior 0.1 ms step; do not tune neural/control
parameters to improve measured learning outcomes.

### Mechanical revision 2, before completing the cohort

The terraced scene failed with MuJoCo BADQACC at both 0.5 ms and the original
0.1 ms timestep. All three reference-timestep seeds stopped during acquisition;
these are integration failures, not negative learning results. Partial records
are retained in `results/light_garden_coarse_failed` and
`results/light_garden_reference_failed`, with their original logs beside them.

Revision 2 removes terraces, rocks, borders and old odor markers, leaving a flat
physical floor and the two light cues in a fully rendered 3D scene. This narrows
the experiment to ground walking without obstacle negotiation. Cue positions,
food radius, neural inputs, learning rule, controller and all acquisition/test
schedules remain unchanged. Use 0.1 ms physics for every final condition. Before
the cohort, body-only tests exercise constant steering at -0.3, 0 and +0.3 for
the full 2.4 seconds, including both controller limits. This is a stability
check, not a numerical convergence study or evidence of learning.

## Biological context

[Vogt et al. 2014](https://pmc.ncbi.nlm.nih.gov/articles/PMC4135349/) provides
evidence for visual appetitive associations involving mushroom-body and dopamine
circuits. [Visual KC connectivity work](https://www.nature.com/articles/s41467-024-49616-z)
provides anatomical motivation, not validation of our artificial color mapping.
This is cue learning, distinct from demonstrating a general spatial-navigation
memory or a complete uploaded fly.
