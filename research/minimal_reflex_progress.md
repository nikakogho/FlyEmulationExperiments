# Minimal reflex: calibration finding and executable assay

2026-09-09. **M3 is incomplete. No neural reflex or learning was demonstrated.**

The exact FANC route resolved in the previous step remains an anatomical result:
five claw-extension afferents, 58 synaptic records, motor ID
`648518346496932836`, main tibia flexor, source rank 3. Rank 3 has not been
cross-identified with a physiologically measured slow/intermediate/fast unit.
Contact counts do not determine conductance, firing threshold or muscle force.

## What the physiology changes

[Azevedo et al. 2020, especially Figure 6](https://elifesciences.org/articles/56754)
reports excitation of flexor motor neurons during passive extension, with
different response strengths across motor types. Excitation often remains below
spike threshold in fast and intermediate units; fast units did not produce
feedback-evoked spikes in those experiments. Slow-unit firing is sensitive to
small movements. Thus a silent motor response can be compatible with physiology.
We cannot select an arbitrary gain that forces the chosen anatomical cell to
correct a displacement and call that a replication.

The [Mamiya et al. 2023 sensory dataset](https://datadryad.org/dataset/doi:10.5061/dryad.dbrv15f6q)
is a candidate source for position-response calibration. Its 6.11 MB archive is
listed publicly, but requests here returned HTTP 403 through the file stream and
HTTP 401 through the API download. Metadata and expected hash are recorded in
the report. No numeric sensory fit was performed. Calcium measurements must stay
in their measured units unless a separately justified observation model relates
them to firing; population curves also do not identify the five anatomical cells.

## Delivered and executed

- `flyplasticity/reflex_assay.py`: offline analysis of matched intact,
  sensory-disconnected and motor-disconnected traces. Requires the same release
  time grid, starting angle and external torque; rejects residual delivered
  output in the motor-disconnected trace. Scores time-averaged absolute angle
  error and final correction. The reference angle exists only in this evaluator.
- Separate checks for excitation without spikes and held-out prediction error
  against a baseline. These checks are tools for validation, not fitted models.
- Six new tests cover correction depending on both cuts, passive return,
  wrong-direction movement, overshoot, mismatched/nonfinite traces, subthreshold
  excitation and baseline comparison. The full offline suite passes 81 tests.
- A mechanical-only 500 ms trial in the actual FlyGym foreleg geometry, initialized
  approximately one degree more extended with zero velocity and both actuators
  off. Initial and final displacement: 0.999997655 degrees. Passive correction:
  **0 degrees**. The evaluator rejects identical copies of this trace as a reflex.
  This is one mechanical trial reused for a negative software check, not three
  biological ablation experiments. Native masses/damping remain uncalibrated.

Evidence: `results/reflex_readiness/report.json`, `mechanical_null.json`,
`guard_events.json`, `unit_tests.log`.

Run from the repository root, using a fresh output directory:

```powershell
.venv/Scripts/python.exe scripts/reflex_readiness.py --out results/reflex_readiness_repeat
.venv/Scripts/python.exe -m unittest discover -s tests -v
```

## Remaining work before the reflex experiment

1. Establish the selected motor unit's physiological identity or explicitly select
   a different, supported sensory-to-motor route. Do not infer identity from rank.
2. Obtain independent sensory and motor recordings and fit the appropriate
   observation, recruitment and force models. Hold out animals/trials rather than
   adjacent samples from the same trace; record units and measurement compartment.
3. Validate joint mechanics, latency and response magnitude. Specify actual
   neural telemetry, numerical limits and exposure protocol before execution.
4. Run one bounded intact trial, inspect it, then consider matched causal cuts.
   The assay assumes the cuts are correctly implemented; it cannot establish that
   from angle traces. Starting velocities, actuator state and all non-ablated
   model parameters must also match in the eventual runner.

Neither a small displacement nor a chosen activity ceiling is established here
as biologically harmless. All execution in this step was mechanical or offline
array analysis, with **zero neural steps**, no needs/valence dynamics and no
aversive training. The mechanical guard recorded 500 observations without a stop;
this is not a neural welfare assessment or evidence of absence of suffering.
The existing prohibition on attaching an uncalibrated neural model remains active.
