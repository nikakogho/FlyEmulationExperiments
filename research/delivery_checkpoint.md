# 3D delivery checkpoint: mechanical preview, neural learning incomplete

2026-09-09. This is not completion of the seven-step learning deliverable.
There is now a runnable 3D replay and a verified video of physical walking,
turning and rest. Its locomotion is explicitly scripted; no learning is claimed.

## Run and view

Double-click `view-arena.cmd` in the repository root. Space plays/pauses, left/right
arrows select a frame, R rewinds, and the mouse orbits/zooms the camera. The
viewer opens paused. It replays recorded physical states and does not advance
physics or neurons. The GUI was launched and closed in a three-second smoke test.

Video: `results/delivery_arena/fly_in_3d.mp4`, 960x608, 280 decoded frames at
25 fps, showing 2.8 simulated seconds at 0.25x speed. Rendering uses the recorded
states only, with no new neural or physical simulation. An inspected frame shows
the full fly clearly; the camera follows its body for display only.

To reconstruct the ignored binary/media artifacts after a clone:

```powershell
.venv/Scripts/python.exe scripts/deliver_arena.py --out results/delivery_arena_repeat
.venv/Scripts/python.exe scripts/view_delivery.py --path results/delivery_arena_repeat --video
.venv/Scripts/python.exe scripts/view_delivery.py --path results/delivery_arena_repeat
```

The existing setup and dependency lock provide FlyGym/MuJoCo. No connectome or
neural model is loaded by these commands. The native model includes meshes and
textures and is over 100 MB, so it is kept local, not committed. The replay tape
and compressed full guard log are also ignored; code and compact evidence are
committed. This preview has no interactive training mode.

## Mechanical results

The arena run advances 28,000 physical steps. Maximum displacement from the
starting point is 16.09 mm. During the final standing window, displacement is
0.00077 mm and median speed is 0.00697 mm/s, passing the existing rest-capability
criterion. A synthetic incoherent-telemetry event prevents the next physical
step. These are mechanical checks, not a neural welfare assessment.

`calibrate_probe_physics.py` fits a nonnegative force pulse through the published
probe mass, spring and damping, rather than equating displacement and force.
The fit uses the clean 22A08 recording's training trials only. Evaluation
displacement RMSE is 0.638 um. Fitted force peaks at 0.875 uN. MuJoCo's prediction
agrees with an independently discretized linear dynamics calculation to within
0.00734 um over the test window. The modeled force pulse is descriptive, not a
recovered muscle activation mechanism.

The actual experimental contact lever arm is not established by these archives.
It is therefore not filled with the FlyGym segment length and called measured.
Full limb-force conversion remains incomplete; the walking controller does not
use this probe fit as if it supplied all six legs' motor physiology.

## Sensory calibration attempt and failed test

The [Mamiya et al. proprioceptor archive](https://datadryad.org/dataset/doi:10.5061/dryad.dbrv15f6q)
downloaded successfully and matched its SHA-256. Its pinned JR688 claw-extension
data contain 28 cells from six flies. A four-parameter population position-tuning
curve was fitted to flies 1-5 (24 cells) and evaluated on fly 6 (four cells).
Evaluation RMSE is **0.359 normalized DR/R**, worse than the training-mean
baseline **0.334**. The validation script returns exit code 1 and retains the
failed outcome. No parameter was adjusted to make this evaluation pass.

This rejects that particular population model. It does not show that accurate
proprioception is impossible. Cell-specific topography, hysteresis and reporter
kinetics are plausible missing components, requiring further model development
and an independent evaluation set. The archive measures calcium fluorescence,
not spikes; even a successful calcium fit would not identify spike rates or the
five selected FANC cells. Deserialization permits only the pinned NumPy array
types and rejects arbitrary globals; no downloaded notebook was executed.

## Seven-step status

| Step | Current status |
|---|---|
| 1: calibrated physical leg/probe | Probe calibrated and numerically checked; limb contact conversion incomplete |
| 2: neural sensory-motor loop | Not run; sensory-to-spike and synaptic recruitment remain unsupported |
| 3: 3D walking arena | Mechanical recording/replay and rest pass; neural-command integration pending |
| 4: sensory-guided behavior | Not demonstrated in the new guarded delivery path |
| 5: associative learning | Existing local-plasticity code retained; no new validated integrated protocol |
| 6: controlled behavioral test | Not run; prior negative outcomes preserved |
| 7: full environment/evidence video | Mechanical preview delivered; requested learning deliverable incomplete |

The next neural run cannot be justified by turning unknown telemetry into false
flags or by treating arbitrary sensory gains as calibrated physiology. The
existing visual-route audit also lacks a validated transfer function and fine
modulatory assignment. A literature refresh found a recent
[aMe12 calcium-imaging preprint](https://www.biorxiv.org/content/10.64898/2026.06.16.732444v1.full)
as a potential source lead; its full text/data were not obtained here, and its
existence is not a completed calibration. No claim is made that no useful data
exist elsewhere.

**99 offline software tests pass.** The sensory empirical test fails. Zero new
neural steps, sensory exposures or aversive training occurred. The full seven-step
task remains open; this file records evidence and limits, not a successful release.
