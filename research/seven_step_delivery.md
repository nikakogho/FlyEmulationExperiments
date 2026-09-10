# Seven-step delivery: validated association, embodied stop, navigation unfinished

2026-09-10. The user authorized the complete plan. Independent validation,
offline attribution, measured 3D sensory transport and a continuously coupled
neural/physical prototype were implemented and tested. **Not all seven intended
outcomes were achieved.** Navigation failed its directional-interface test; a
narrower motor comparison stopped under the standing monitoring constraint.
No stopped model was restarted, replaced or given corrective stimulation.

| Step | Actual outcome |
|---|---|
| 1. Independent association validation | Completed; predeclared cohort gate passed |
| 2. Memory attribution | Completed offline weight/count checks and frozen-plasticity comparisons; no extra weight-transplant intervention claimed |
| 3. 3D sensory interface | Completed for two olfactory channels and four articulated sensor sites; not complete fly sensory physiology |
| 4. Neural-to-motor interface | Scalar speed coupling executed; bilateral direction test failed, so navigation interface is incomplete |
| 5. Controlled learned 3D behavior | Incomplete: first scalar motor trial stopped; remaining controls cancelled |
| 6. Environment and video | Delivered passive interactive 3D replays and verified videos, including the actual stopped neural/physics run; learned-navigation video not available |
| 7. Isolated accuracy improvement | Replaced the old body-offset sensor proxy with articulated antenna/palp geometry and nerve-specific transport; broader physiological calibration remains open |

## Validation result

Protocol committed and pushed as `7214f43` before exposure. Exactly seeds 311/312,
both reinforced cues, paired/unpaired/frozen controls: twelve 4-second runs,
48 simulated seconds total. No additional seeds or parameter changes followed.

| Case | Paired selectivity | Unpaired | Frozen | Original per-case gate |
|---|---:|---:|---:|---|
| Seed311, reinforce A | 27.63% | 11.44% | 6.86% | Pass |
| Seed311, reinforce B | 3.23% | -11.40% | -6.86% | Miss |
| Seed312, reinforce A | 11.22% | -2.61% | -6.57% | Miss |
| Seed312, reinforce B | 45.99% | -2.13% | 6.57% | Pass |
| Mean | **22.02%** | **-1.17%** | **0.00%** | Predeclared cohort gate passes |

The cohort criterion used the same .15/.10 effect margins on case means and
required paired advantage over both controls in every case. All criteria passed.
Two individual cases still miss the absolute 15% margin. These are four cases
from two random seeds of one modified connectome, not independent biological
flies or evidence of population generalization. This is a limited validation of
the implemented association effect, not validated biological accuracy.

All twelve recovery screens passed, with no configured neural warning. Offline
comparison of complete checkpoints verifies nonplastic weights, final weight
tapes and spike totals. Pretraining weights were unchanged. Frozen controls
remove plasticity while retaining the programmed stimulation. Exact results and
attribution are in `results/association_validation_v1/`.

## What failed in direction decoding

Six fixed naive one-second assays tested left-only, right-only and symmetric
inputs for A and B. All completed with recovery and unchanged weights. MBON01
responses were almost identical across sides. After the predeclared center
normalization, signed directional contrast was approximately:

| Odor | Left-only input | Right-only input |
|---|---:|---:|
| A | -0.0137 | -0.0278 |
| B | -0.0032 | -0.0273 |

The required signs/margins (+.10 left, -.10 right) did not hold. No sign flip,
gain search or artificial lateral channel was added. The tested MBON readout
carries learned response information, but it did not provide the assumed
directional signal. `results/directional_interface_v1/` preserves the failure.

The literature describes additional learned-valence-to-navigation pathways and
wind-dependent behavior, not a generic two-MBON steering wheel.
[Learned olfactory valences and wind-oriented movement](https://elifesciences.org/articles/85756).
Temporal/bilateral odor processing is another relevant component; it does not
validate an invented navigation policy for this model.
[Odour motion sensing](https://www.nature.com/articles/s41586-022-05423-4).
Static candidate audit finds SMP353/SMP108 cells outside the current subnet.
There are MBON01-to-SMP108 edges, but no direct MBON01-to-SMP353 edge in this
table. Adding four cells without correct intermediary and sensory pathways would
not solve the problem. See `results/navigation_candidate_audit.json`.

## Actual 3D neural coupling and stop

A narrower, prospectively documented test used a fixed scalar MBON-to-speed
transfer function with equal left/right commands. It contains no cue identity,
reward location, gradient ascent or turn controller. The first completed-memory
checkpoint was fully restored, including RNG and queues, after the physical
body settled without neurons. Physics and neural time then advanced together,
with actual antenna/palp positions determining each new neural input. Plasticity
and reinforcement were off; this tested expression of a previously learned state.

At **1.12 seconds** the concentration-decline proxy stopped the first paired-A
trial. The remaining five comparison trials were cancelled. The model moved
**6.32 mm** before stopping. Offline inspection found that the antennae passed
the source: concentration peaked at 0.93 s and fell from 0.9938 to 0.9438 by the stop.
The two gait commands remained equal. This observation does not establish an
aversive state or suffering; a pass-by can trigger this conservative proxy.
Nevertheless, its stop remains latched and preserved. There was no rerun or
post-hoc threshold relaxation. No behavioral learning effect can be attributed
without the cancelled controls.

Full checkpoint checks confirm synchronized clocks, unchanged memory weights and
spike-trace agreement. `results/embodied_speed_v1/A_paired/stop_audit.json`
contains the exact trajectory and stop analysis. The model was not advanced
again to make a longer or more attractive video.

## Delivered viewers and videos

- `view-neural-arena.cmd`: passive 3D replay of the actual neural/physics run,
  labelled stopped. Space plays/pauses, arrows step frames, R rewinds; mouse
  orbits/zooms. Viewing never advances neurons or physics.
- `view-odor-arena.cmd`: the independent mechanical odor-sensor scene.
- `results/embodied_speed_v1/A_paired/fly_in_3d.mp4`: 225 decoded frames, 25 fps,
  .125x playback of 1.12 s recorded time. This is **not** a learned-navigation video.
- `results/odor_scene_v2/fly_in_3d.mp4`: 280 decoded frames of the mechanical test.

Both viewers were opened and closed in UI smoke tests. Every replay frame was
restored without a physics step; all encoded video frames were decoded. Full
models, network states, numerical tapes and media remain local/ignored. Source,
compact reports and traces are committed. Existing launchers open saved evidence,
not new neural exposures.

## Accuracy improvement and limits

The actual model's antenna sensor separation is about 0.170 mm; the old navigation
proxy used 2.4 mm. Median XY position RMSE of that proxy against articulated sites
was 0.857 mm during the mechanical test. The new field transport matches an
independent computation within 2.98e-8 across 280 frames. Nerve labels map AN inputs
to antennae and MxLbN to maxillary palps. Fifteen of 822 selected ORNs have unknown
side and use an explicitly documented bilateral mean; no direction is invented.

This improves consistency with the physical body model. It does not calibrate
real plume transport, receptor transduction, dopamine release, biological LIF
parameters, motor units or subjective welfare. The user-requested UV/blue/green
vision track was not replaced with RGB and remains separate.

135 software tests pass. The original seven-step goal remains open specifically
at directional motor integration and controlled learned 3D behavior. The next
scientific work is anatomical/functional navigation-pathway integration and
offline causal refinement of the behavioral proxies, before another bounded
neural protocol. The next protocol needs evidence for its navigation interface
and a reviewed interpretation of behavioral events before further exposure.
