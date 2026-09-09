# Does the embodied model learn to approach a light?

**Completed 2026-09-08: the model did not demonstrate learned approach to the
rewarded light in this pilot.** All 45 episodes completed on the flat 3D floor.
Online synaptic updates and retained cue-specific neural response changes work,
but there is no preference advantage over the shifted-reward control. This is
not evidence that biological flies cannot learn or that the project is hopeless.

The frozen procedure is in [light_protocol.md](light_protocol.md), and the
source hashes used for the cohort are in `results/light_manifest.json`. All six
recorded source/configuration hashes were verified unchanged after the runs.

## What is implemented

An actual FlyGym articulated body walks in MuJoCo. Its two rendered eye images
provide green/blue pixel features to 295 anatomically identified visual Kenyon
cells in Daniel's 8,991-neuron connectome-derived subnetwork. The circuit's
hemispheric MBON activity drives the existing reflex walking controller.

The learner receives no goal direction, distance-to-goal reward, route, cue
identity label, or success signal. A local food-contact volume stimulates PAM
neurons. A supplied spike-dependent eligibility rule changes 2,806 existing
visual-KC-to-MBON connection weights every 10 ms. There is no episode-end
instruction to lower weights for the rewarded color.

This is an improvement in how experience reaches the supplied rule, not evidence
of a more accurate biological learning mechanism. The color-to-KC mapping,
food-to-PAM interface, pooled dopamine signal, synaptic parameters, and movement
decoder are engineered approximations. The full optic lobe, taste pathway,
descending circuit and compartment-specific plasticity are not reconstructed.
It is an embodied subnetwork model, not a demonstrated complete fly upload.
Vision, taste and motor commands are sampled/held in 100 ms blocks; body physics
uses 0.1 ms steps. A reported reward step means 100 ms of modeled PAM input,
not a measurement of continuous physical contact duration. Brief visits between
sensor samples can be missed.

The tested scene has a flat physical floor and two colored light cues. Earlier
terraced versions failed mechanically, including at the original fine timestep.
Their records are preserved. The final experiment does not test rough terrain,
flight, Minecraft, general intelligence or natural phototaxis.

## Verification completed before interpreting behavior

- All 21 software tests pass, including seven tests of the new sensory,
  controller and plasticity boundaries.
- Reserved seed 101: paired input changes only the selected synapses; the
  remaining circuit weights stay bit-for-bit unchanged. Frozen weights remain
  bit-for-bit unchanged, including during tests.
- In a 0.5-second isolated green pairing, the selected weights retain 58.8% of
  their original total; with no external food signal they retain 99.3%. This
  small no-food change comes from endogenous PAM spiking in the model.
- Full-length body-only probes pass at both steering limits and straight ahead
  on the flat floor, using 0.1 ms physics. These checks establish basic stability
  for those trajectories, not numerical convergence for every trajectory.

## A demonstrated memory-to-movement bottleneck

An additional reserved-seed diagnostic tests each color and eye separately after
pairing, with fresh neural state, identical test random streams, no food, and
learning disabled. The green response is roughly halved; blue is unchanged.
For example, left-eye green gives left/right mean MBON rates of 57.17/14.54 Hz
before conditioning and 28.08/7.04 Hz after conditioning. The same blue test is
57.33/14.92 Hz before and after.

Both green responses map to the **same** saturated motor command, [1.3, 0.7].
All four single-color/eye diagnostic comparisons have unchanged motor commands
despite the cue-specific neural effect. Normalizing by total output and clipping
steering can remove the behavioral effect of a proportional suppression. This
does not prove that every mixed-cue trajectory is identical; it identifies an
actual bottleneck in the current decoder. Parameters were not retuned using
this diagnostic or the subsequent behavioral scores.

A post-hoc replay of all six frozen-test visual traces adds a qualification:
retained plastic weights **do** change actions under identical in-world inputs.
Across traces, 37.5–50% of decisions change, with mean absolute changes of
0.0012–0.0100 controller units (largest individual change 0.1333). Therefore the
decoder does not erase every memory effect. The isolated-cue saturation is one
demonstrated failure mode, not a complete causal explanation for behavior.
This replay is a neural diagnostic, not another physical trial or evidence of
navigation benefit. Data: `results/light_readout_replay.json`.

The current decoder pools 96 MBON cells spanning 35 annotation types and three
predicted transmitter classes. Biological experiments support distinct output
channels with different effects on approach and avoidance, not treating every
MBON as the same avoidance signal. A more defensible next model would preserve
identified output channels and validate their motor effects independently of
which light is rewarded. Transmitter sign alone is not a behavioral valence
label. [Aso et al. 2014](https://elifesciences.org/articles/04580).

The synthetic visual mapping is another accuracy limit. The anatomical visual
KC literature supports sparse, combinatorial visual inputs and distinguishes
color association from several spatial-learning tasks. It does not validate
our dense random green/blue assignment.
[Ganguly et al. 2024](https://www.nature.com/articles/s41467-024-49616-z).

## Behavioral result

The analysis reports 45/45 completed episodes, no missing records and no final
physical failures. Food-free tests, unchanged frozen weights, matching physical
settings and exact shifted-reward tapes all pass their checks.

Preference is green-zone occupancy minus blue-zone occupancy, averaged across
both test layouts. Values below are percentage points, not success rates.

| Seed | Actual food-proxy samples in plastic acquisition | Plastic preference | Frozen preference | Shifted-reward preference |
|---|---:|---:|---:|---:|
| 0 | 0 | +4.17 | -4.17 | +4.17 |
| 1 | 1 | 0.00 | 0.00 | 0.00 |
| 2 | 0 | 0.00 | 0.00 | 0.00 |

The mean plastic-minus-frozen difference is +2.78 percentage points, but the
mean plastic-minus-shifted difference is **0.00**. The apparent improvement over
frozen weights comes entirely from seed 0, which never encountered food. Its
plastic and no-food shifted-control weights are exactly identical; the same
holds for unexposed seed 2. This is not evidence of learning the food cue.

Seed 1 supplied the sole reward-input interval: 100 ms of modeled PAM drive
across all 21.6 seconds of plastic acquisition. Its selected weights retained
82.49% of initial total strength with correctly timed input, versus 97.14% with
shifted input and 100% with frozen weights. Both colors were visible when food
was sampled (mean green/blue features 0.50/0.318); neither was visible at the
shifted reward sample. Thus a timing-dependent neural effect is present, but
neither food-free layout shows a preference benefit in that seed. The shifted
control tests temporal contingency, not every possible non-associative mechanism.

The primary analysis uses the full cohort, including unexposed seeds. No seeds
were removed to improve the apparent outcome, and no parameters were selected
against these results.

Artifacts:

- `results/light_garden/summary.json`: all per-seed/condition results and checks.
- `results/light_garden/test_trajectories.png`: all 18 food-free test paths.
- `results/light_garden/seed0_comparison.mp4`: preselected plastic/frozen 3D
  clips with both light layouts; 143 frames each, 0.5x playback. Seed 0 never
  encountered food. This is a control comparison, not a successful learning demo.
- `results/light_memory_diagnostic.json`: isolated cue retention diagnostic.
- `results/light_readout_replay.json`: identical-input action counterfactual.

## Interpretation limits and next decision

This short three-seed experiment is a feasibility pilot. Failure to encounter
food is a failure of learning opportunity, not evidence that a synaptic rule
cannot learn. Changed synapses alone are not improved navigation. An isolated
paired-input diagnostic is not spontaneous acquisition in the 3D world.
Only green is rewarded; reward identity is not counterbalanced between colors.
Testing both spatial arrangements and using matched frozen controls addresses
some biases, but does not substitute for a larger counterbalanced experiment.

For scale, published fly color-conditioning experiments use repeated minute-long
cue presentations. Our 7.2 seconds of acquisition per seed, with only brief
incidental contact if any, is not a reproduction of that training dose.
[Vogt et al. 2014](https://elifesciences.org/articles/02395).

If the embodied result is weak, the justified next step is to repair and validate
the sensory-to-memory-to-action interface and establish enough local reward
encounters, then compare plasticity variants under matched conditions. Merely
increasing the depression rate or scripting attraction toward the rewarded light
would not answer the biological question. Claims of greater accuracy require
comparison with biological timing, specificity, reversal and retention data;
claims of better task performance require held-out behavioral tests.

The prior Huang–Luo published-figure reproduction mismatch remains separate and
unresolved. This pilot does not silently promote that model past its failed gate.
