# First sensory-apparatus milestone

2026-09-21. The first deliverable from `sensory_environment_recommendations.md`
is complete: one short 3D mechanical walk, synchronized spectral-eye/body/odor
recordings, automated consistency checks, and a comparison video. No connectome,
isolated neural visual model, reinforcement or plasticity was run.

## What runs

The existing MuJoCo/FlyGym body uses the fixed engineering standing/gait
controller. After 0.3 s mechanical settling, it records 3 s: rest 0-.3, forward
.3-1.1, turn 1.1-1.6, forward 1.6-2.1, rest 2.1-3 s. Commands are prescribed;
this is not spontaneous exploration or learned movement.

The flat scene has a spectral floor pattern, three visual-only UV/blue/green
cards, and a visual marker for a synthetic odor tracer. All surfaces receive
explicit spectra. The tiles/cards cannot generate physical contacts: both
collision masks and compiled contact pairs are checked, and contacts are
inspected during every 0.1 ms physics step. Human-display RGB does not control
the spectral input. The cards are optical fixtures, not physical obstacles.

Every 10 ms, with no physical step between modalities, the recorder captures:

- Both eyes: 721 ommatidial samples each, outer Rh1 plus mosaic-selected R7/R8.
- 42 joint angles and velocities; 36 contact-force vectors.
- Four synthetic-tracer concentrations at actual L/R palp and antenna positions.
- Acquisition times and the preceding motor command.

Eyes and odor remain active during rest. No background input is switched off to
make the model look quiet. Missing taste, wind receptors, hearing, thermal and
humidity receptors, ocelli and neural proprioception are explicitly unavailable.
Body position/source coordinates remain in evaluator records, not the peripheral
packet API. Arrays are immutable snapshots; missing/stale timestamps, changed
layouts, invalid ranges and nonfinite samples are rejected.

## Measured results

| Check | Result |
|---|---|
| Software suite | 174 tests pass, including seven new packet/projection tests |
| Recording | 301 samples, 100 Hz, three seconds plus prior settling |
| Actual camera projection | 20 rendered targets; maximum error 0.270674 pixels, limit 1.5 |
| Same-state repeated optics | Exact equality |
| Randomized display RGB | Exact same spectral samples |
| Actual-camera occlusion | Both eyes: 12 visible pixels -> 0 -> 12 restored |
| Independent joint-state audit | Max angle error 1.19e-7 rad; velocity error 3.59e-6 rad/s |
| Position-to-odor audit | Max error 2.97e-8 in normalized concentration |
| Rest, final 0.3 s | Displacement 0.00323 mm; median speed 0.0230 mm/s |
| Existing mechanical rest limits | <=0.2 mm displacement and <=0.5 mm/s median speed: pass |
| Overall body displacement | 14.966 mm; the prescribed turn is detectable |
| Repeated full fixture | Exact equality of all saved sensory and qpos/qvel/act arrays |
| Passive viewer | All frames restored; native launch/close check passed |
| Video | All 301 frames decoded, 25 fps, 12.04 s at 0.25x playback |

Timing/geometry checks are engineering checks, not biological accuracy bounds.
The deterministic repeat tests software reproducibility, not independent animal
or seed replication. Full first recording took about 102 s wall time; an audit
of saved measurements takes under a second on this host. These are measured
local timings, not promised neural simulation throughput.

## Preserved implementation failures

`sensory_scene_v1` failed before recording samples because dm_control required
its wrapped render-option object rather than the native MuJoCo object. The
corrected v2 recording passed. The failed report and its source hash are retained.

`sensory_occlusion_v1` initially left four target pixels visible. Investigation
showed the compiled `geom_sameframe` shortcut caused MuJoCo to ignore the
blocker's edited quaternion: rotation error was about 1. Setting the shortcut
to zero made the actual matrix agree within 3.6e-16. The corrected test explicitly
asserts that agreement and restores every edited model field. Both occlusion
attempts used zero physics integration and zero neural steps. Their results
are separate from the walk; no failing sensory criterion was loosened.

## What is not yet realistic

Spectral excitation still uses the existing normalized ERG filters over
315-550 nm and approximate retinal geometry/mosaic. It does not add missing
long-wavelength sensitivity, phototransduction/adaptation, calibrated absolute
intensity, full illumination/shadows, six individually mapped outer receptors,
color opponency or neural vision. The false-color eye panels show the actual
saved samples with fixed per-channel display scales; they are not RGB eye input.

The odor is a normalized static Gaussian tracer with sigma 4 mm, not a named
odor, moving plume or calibrated ORN response. Contact vectors are mechanical
loads in native FlyGym units. They are not touch firing rates or evidence of
proprioceptive perception. The body controller is still engineered.

No neural system was exposed in this work. Passing apparatus tests is neither
a welfare assessment nor permission to treat future neural integration as safe.
All historical neural stops and failed learning gates remain unchanged.

## Files and reproduction

- `results/sensory_scene_v2/sensory_walk.mp4`: synchronized video.
- `results/sensory_scene_v2/preview_130.png`: sample composite at the turn.
- `results/sensory_scene_v2/audit.json`: all consistency checks.
- `results/sensory_scene_v2_repeat/reproducibility.json`: exact repeat comparison.
- `results/sensory_occlusion_v2/checks.json`: actual rendered occlusion checks.
- `view-sensory-scene.cmd`: passive 3D orbit/zoom viewer for the saved body.
- `scripts/sensory_fixture.py`: scene and optical sampler.
- `flyplasticity/sensory_recording.py`: immutable peripheral packet and timing gate.

```powershell
.venv/Scripts/python.exe -m unittest discover -s tests -v
.venv/Scripts/python.exe scripts/audit_sensory_recording.py --path results/sensory_scene_v2
.venv/Scripts/python.exe scripts/render_sensory_recording.py --path results/sensory_scene_v2
# Optional new mechanical fixture; refuses an existing output directory:
.venv/Scripts/python.exe scripts/record_sensory_scene.py --out results/my_new_sensory_fixture
```

Code, tests, source provenance and compact reports are versioned. Media, compiled
scene and array archives remain local and ignored. Source hashes identify the
installed FlyGym geometry and existing spectral data used by each recording.

## Next bounded improvement

This now supplies a fixed input recording and fast benchmark for sensory changes.
Next audit the available spectral source data beyond 550 nm and the retinal
angular acceptance function; preserve unavailable regions rather than inventing
tails. Separately obtain temporal response measurements for fitting a minimal
adaptation model. Compare candidates on development recordings, then evaluate a
reserved set of scene bearings/spectra. A new neural protocol is not yet admitted:
pathway mapping, physiological transfer and welfare review remain separate gates.
