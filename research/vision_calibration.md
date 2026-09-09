# Offline visual-pathway calibration

We now have the authors' fitted FlyVis visual model running locally, with a
reproducible stimulus-response check. It passed all eight tested expected-motion
direction checks at both time steps, but failed one polarity check. It remains
disconnected from the body and LightBrain. Better learning is not demonstrated.

## Model and biological rationale

T4 and T5 provide a biologically motivated target for motion calibration:
their subtypes encode motion directions, with different ON/OFF preferences.
[Primary experimental study](https://www.nature.com/articles/nature12320).
We used the published connectome-constrained, task-optimized FlyVis model,
not a newly invented pixel-to-steering rule. Its fitted parameters are an
additional functional assumption, not information recovered from synapse
counts alone. [Model paper](https://www.nature.com/articles/s41586-024-07939-3),
[authors' implementation](https://github.com/TuragaLab/flyvis).

The pinned code is commit `92b3845cc426dd309a1a0e1b3890156c42e14021`.
Checkpoint `flow/0000/000` is the upstream default; no alternate checkpoint
was selected after seeing results. The archive matched the authors' SHA256
`71c78d4070556a536b13b23ee3139cd2788aa2a9d07d430a223b4edead281db1`.
The visual subsystem has 45,669 nodes. This is a separate visual model, not
an expansion already integrated into the 8,991-neuron learning subnet.

## Fixed tests and results

See [the protocol](vision_calibration_protocol.md), written before response
inspection. Eight movies cover four cardinal directions and two polarities;
one additional movie supplies constant gray input. Measurements use the
central neuron of each T4/T5 subtype. These are synthetic retinal stimuli,
not yet images mapped from our 3D body's eyes.

| Check | 200 Hz | 400 Hz |
|---|---|---|
| Preferred versus opposite motion direction | 8/8 pass | 8/8 pass |
| Expected versus other edge polarity | 7/8 pass | 7/8 pass |
| Constant-gray central-cell stability | Pass | Pass |
| Finite responses across all simulated nodes | Pass | Pass |
| Neural parameter checksum unchanged | Pass | Pass |
| Overall qualitative gate | **Fail** | **Fail** |

T4d is the polarity failure. At 400 Hz, its maximum positive response to an
ON edge was 0.1041 model units, versus 0.2951 for an OFF edge. Its expected
ON-motion direction selectivity nevertheless passed (index 0.9969). The larger
OFF response is not explained by a late maximum in the post-stimulus tail:
at 200 Hz its maximum was during edge motion, 0.30 s after onset.

Halving the time step changed direction indices by at most 0.00722 and
preferred-direction peaks by at most 5.47%, within the preset numerical
tolerances. The same polarity failure persisted. This makes a coarse-time-step
artifact less likely; it does not resolve the mismatch.

Our polarity criterion is an engineering gate, not a claim that every real
T4 neuron must have zero OFF response or that this invalidates the published
model. Diagnosing the mismatch requires comparing the exact stimulus and
response metric with the paper's analysis. No parameters were tuned to these
stimuli. A passed motion check also does not validate color processing,
phototaxis, or a connection from T4/T5 to visual Kenyon cells.

## Software validation and evidence

All 36 existing unit tests pass. One additional test in the separate vision
environment checks numeric/string/scalar HDF5 round trips and closed handles.
The initial attempt exposed a Windows incompatibility in datamate 1.0.0:
its writer tried to unlink an open HDF5 file. `scripts/flyvis_windows.py`
replaces only that storage operation with a context-managed write, leaving
model equations and parameters unchanged. The initial traceback and failed
cache are preserved. The upstream checkout itself is unmodified.

An initial attempt to collect the new storage test in the base environment
failed because that environment lacks h5py; the test now lives under
`tests/vision` and runs explicitly in the isolated vision environment.

- `results/vision_calibration_v1/`: 200 Hz checks, traces and executed runner snapshot.
- `results/vision_calibration_dt2500us/`: 400 Hz checks and traces.
- `results/vision_comparison/`: numerical comparison and polarity chart.
- `results/vision_base_tests.log`, `results/vision_storage_tests.log`: passing tests.
- `requirements-vision-lock.txt`: isolated CPU environment versions.

```powershell
./setup-vision.ps1
.venv/Scripts/python.exe -m unittest discover -s tests -v
.venv-vision/Scripts/python.exe -m unittest discover -s tests/vision -v
.venv-vision/Scripts/python.exe scripts/calibrate_flyvis.py --out results/my_new_vision_run
.venv-vision/Scripts/python.exe scripts/calibrate_flyvis.py --dt .0025 --out results/my_new_fine_vision_run
```

Calibration refuses to overwrite its output directory and currently returns
exit code 1 because of the recorded biological-tuning gate, not a crash.
`scripts/compare_vision_timesteps.py` compares the two fixed recorded runs and
also returns 1 while that gate fails. Cached 400 Hz execution took 52.75 seconds
on CPU using two Torch threads; this is offline performance, not closed-loop
real-time throughput. The RTX GPU was not needed for this calibration.

## Decision

We reproduced a useful motion-sensitive visual subsystem, with one explicit
unresolved tuning discrepancy. Keep full-brain integration off. The next
bounded investigation is to reproduce the authors' exact T4d polarity metric
and inspect retinal-coordinate mapping before connecting any visual output.
Do not replace the existing synthetic visual-KC input with arbitrary T4/T5
currents and call it anatomically faithful.

No whole-brain, body, reward, punishment or learning simulation ran in this
stage; an isolated fitted visual network did run. These results do not assess
subjective experience or guarantee comfort.

Follow-up: [comparison with the authors' analysis](author_polarity_comparison.md)
confirms the default T4d mismatch under their exact flash metric, but finds
the expected T4d sign in 9/10 of their listed top-model set. All eight ensemble
median signs agree. The original single-checkpoint failure remains recorded;
it is not a failure of the whole ensemble's polarity pattern.
