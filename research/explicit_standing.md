# Explicit mechanical standing

Implemented `flyplasticity/standing.py`: zero descending drive now requests a
neutral leg posture with continuous foot adhesion, using the existing joint
actuators. A 100 ms smooth transition avoids an instantaneous posture command.
Gait oscillation and corrective stepping are bypassed during rest. On resuming
walking, gait amplitude and stale correction state are cleared. The physical
simulation continues normally: no position clamp, velocity overwrite, gravity
change or frozen physics is used. This is an engineered motor controller,
not a recovered biological rest circuit.

## Validation

All 36 unit tests pass, including actuator shape, transition interpolation,
resumption state and invalid command checks. Three independent phase seeds
completed the same 1.4-second rest/walk/rest protocol as the earlier test:
rest to 0.3 s, activity 0.6 until 0.7 s, then rest until 1.4 s. The original
final-0.3-second gate was unchanged: net XY displacement <= 0.2 mm and median
instantaneous XY speed <= 0.5 mm/s.

| Seed | Rest speed (mm/s) | Rest displacement (mm) | Walking speed (mm/s) | Gate |
|---|---:|---:|---:|---|
| 101 | 0.02863 | 0.006512 | 9.584 | Pass |
| 102 | 0.00852 | 0.002011 | 9.852 | Pass |
| 103 | 0.00931 | 0.003156 | 11.300 | Pass |

Walking speeds are medians of samples between 0.32 and 0.7 s. They confirm that
passing rest did not simply disable all movement. Each run recorded 70 fresh
sensory packets, 42 joints and 36 contacts; sampled image timestamps matched
body timestamps. Final body heights were 1.020, 1.108 and 1.119 mm. Full upright
orientation and robustness to different surfaces were not evaluated.

The earlier seed-101 controller had rest speed 0.50415 mm/s and failed. Its
record remains unchanged in `results/sensory_bridge/`. A first implementation
attempt also failed on a joint-array shape mismatch before completing a
physical step; its traceback and partial result are preserved in
`results/standing_v1_seed101.log` and `results/standing_v1_seed101/`.
Using FlyGym's flattened default pose fixed that bug; a regression test checks
the 42-actuator shape.

## Evidence and reproduction

`results/standing_summary/checks.json` contains the metrics and source hashes;
`speed_traces.png` shows instantaneous speeds, including transition transients.
Raw records are in `results/standing_v2_seed101/`, `standing_v2_seed102/` and
`standing_v2_seed103/`. Test output is `results/standing_unit_tests.log`.

```powershell
.venv/Scripts/python.exe -m unittest discover -s tests -v
.venv/Scripts/python.exe scripts/check_explicit_standing.py --seed 101 --out results/my_new_standing_run
.venv/Scripts/python.exe scripts/analyze_standing.py
```

The probe refuses to overwrite an existing output directory. The analysis
summarizes the fixed recorded three-seed cohort, not an arbitrary new run.

## Scope and next step

All trials were mechanical only; no connectome brain or learning model ran.
The rest/walk schedule was externally prescribed. Passing this gate neither
demonstrates autonomous rest nor establishes absence of subjective harm.
Three short flat-floor tests are a limited capability check, not general
locomotor validation.

The next scientific step is offline calibration of one anatomically justified
visual input pathway. The richer sensory transport and standing controller
remain disconnected from LightBrain. Improved learning is still unproven.
