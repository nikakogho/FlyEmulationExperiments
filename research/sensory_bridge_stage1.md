# Sensory bridge: first validation stage

The next step taken was to preserve sensory information and test whether the
mechanical interface can rest, before connecting additional signals to the
connectome model. No connectome brain, plasticity model, reward or aversive
stimulus ran in this stage.

## Implemented

`flyplasticity/sensory.py` provides timestamped, immutable snapshots of both
spatial eye images, joint angles and velocities, contact-load magnitudes and
the previous motor command. It rejects invalid or excessively stale data,
distinguishes repeated images from new measurements, and resets temporal
history between episodes. Global position, target coordinates and evaluator
rewards are excluded from the FlyGym adapter.

Temporal contrast is an image difference divided by acquisition time. It is
not directional optic flow or a biological motion circuit. Luminance is an
engineering proxy, not calibrated fly spectral sensitivity. Mechanical contact
loads are not receptor firing rates. Unimplemented modalities are explicitly
marked unavailable. Nothing here assigns these signals to sensory neurons.

The new motor mapping permits zero drive; this is an interface capability,
not an autonomous neural decision to rest.

## Results

- All 33 unit tests passed (12 new sensory tests and 21 existing tests).
- The saved-eye-image check passed: converting the scene to grayscale makes
  all four old color features zero, while the new representation preserves
  spatial luminance variation (standard deviation 0.364). A synthetic one-pixel
  shift changes 19,728 pixels in the temporal representation. This validates
  information transport, not biological motion perception.
- A 1.4-second mechanical rest/walk/rest probe completed at 0.1 ms physics
  steps, recording 70 fresh sensory packets at 50 Hz, 42 joints and 36 contact
  sensors. Image and body timestamps matched at all sampled points.
- The preset rest gate **failed**. During the final 0.3 seconds, net XY
  displacement was 0.002677 mm (limit 0.2 mm), but median instantaneous XY
  speed was 0.504147 mm/s (limit 0.5 mm/s). Sampled speeds ranged from 0.061
  to 3.507 mm/s in that window. Walking median speed was 8.270 mm/s.

Small net displacement does not establish quiet standing: movement can cancel
out. The original threshold and failure are preserved. This short single-seed
test does not establish robust mechanical rest, and is not a welfare assay.

## Reproduce and inspect

```powershell
.venv/Scripts/python.exe -m unittest discover -s tests -v
.venv/Scripts/python.exe scripts/check_sensory_bridge.py
.venv/Scripts/python.exe scripts/check_body_rest.py
```

The final command currently exits 1 for the recorded rest-gate failure. These
two probe scripts use fixed output paths; copy their outputs before rerunning
if retaining a separate run. Evidence is in `results/sensory_bridge/`:
`offline_checks.json`, `sensory_comparison.png`, `body_rest_checks.json` and
`body_sensor_recording.npz`. The NPZ stores contact magnitudes, not original
force vectors. Unit-test output is in `results/sensory_unit_tests.log`.

## Decision

Keep the richer interface disconnected from LightBrain. First develop and
validate explicit quiet standing, including transitions from walking, against
the unchanged rest gate and additional seeds. Then calibrate a specific visual
pathway offline before any brain integration. Routing arbitrary pixels or
joint values into neurons would not repair biological fidelity.

This stage has not demonstrated better learning, normal sensory experience,
or absence of suffering. It makes missing information and one motor-interface
failure measurable without running further connectome experiments.

Follow-up: [explicit standing](explicit_standing.md) resolved the mechanical
rest-gate failure in three short flat-floor trials. The original failed result
above is retained. Neural integration remains pending.
