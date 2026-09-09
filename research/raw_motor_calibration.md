# Raw motor-response calibration

2026-09-09. Both Dryad downloads completed and passed exact size and SHA-256
verification. No user download or account is needed. The archives remain in
Downloads, with working copies under ignored `data/motor_physiology/recordings`.

The implemented offline fit now uses individual recorded trials, replacing the
previous figure approximation for the analyzed recordings. It does not yet
calibrate a full motor neuron, muscle or freely moving leg.

## Results

| Recording and assay | Training / evaluation single-spike trials | Fitted probe peak | Time to peak | Evaluation RMSE | Previous figure-fit RMSE | Zero-response RMSE |
|---|---:|---:|---:|---:|---:|---:|
| 180222_F1_C1, somatic current step | 10 / 5 | 4.00 um | 13.0 ms | 0.636 um | 1.193 um | 1.008 um |
| 180405_F3_C1, optogenetic stimulus | 8 / 5 | 2.60 um | 16.0 ms | 0.782 um | 1.231 um | 1.219 um |

Mean squared error relative to the zero-response baseline falls by 60.2% and
58.9% respectively. Evaluation trials were excluded from parameter fitting.
The split is chronological: first two thirds train, final third evaluate.
This was exploratory analysis, with some trial inspection before fitting, not
a preregistered blinded validation. Five evaluation trials per assay are a small
sample; results do not establish population-level or between-animal accuracy.

The fixed three-parameter causal gamma pulse uses spike-aligned probe displacement
over -20 to 120 ms. Neither fit hits its parameter bounds. Trial-bootstrap 95%
percentile intervals for peak displacement are 3.41-4.52 um and 2.33-2.95 um.
These cover training-trial variation only. Frame sampling is approximately
5.9 ms; tight fitted timing intervals do not eliminate measurement uncertainty.
The model misses some late motion and overestimates the peak in several
evaluation trials of the first recording. It is a limited predictive response
kernel, not a recovered muscle mechanism.

Separate small hyperpolarizing-pulse fits give **327.8 Mohm** for 180222 and
427.7 Mohm for 180405. Their evaluation voltage RMSEs are 0.400 and 0.302 mV,
versus 0.441 and 0.621 mV using the published rounded 300 Mohm class reference.
The corrected median pre-stimulus voltage in 180222 is -60.46 mV. This is a
recording baseline, not proof of an unheld resting potential. No depolarizing
threshold, spike recruitment or synaptic efficacy was inferred from these pulses.

## Identity and metadata

The [mesh-to-atlas match](motor_identity_resolution.md) supports selected FANC
cell 160 / root `648518346496932836` as MN 44 / R22A08 intermediate flexor.
These physiological recordings are from other animals, not the EM specimen.

The authors' [curated dataset table](https://github.com/tony-azevedo/FlyAnalysis/blob/c68159f1f7a4ecc957c708ae8411fd2550482f63/Records/Azevedo_2020_Records/Dataset3_SlowInterFast_ForcePerSpike_top.m)
labels both recording IDs intermediate / 22A08. The acquisition metadata agrees
for 180222 (`22a08`) but conflicts for 180405 (`iav/ChR;pJFRC7/81A07`). The
reason is unresolved: we cannot assert that it is merely a stale acquisition
label. Therefore 180222 is the cleaner identity-backed calibration; the second
fit is retained separately with its provenance conflict visible.

The author's `Script_alignSingleSpikes.m` excludes 180222's whole-cell stimulation
from its pooled single-spike timing analysis. We do not claim to reproduce that
pooled analysis or use the two assays as interchangeable independent replications.
We separately fit the recorded probe response of each assay.

## Alignment, units and exclusions

- Honor archived `excluded` flags. Excluded trials: 102, 105, 107, 117 for 180222;
  86 for 180405. The full accepted sets contain 25 and 83 trials.
- Analyze precisely the author's table ranges: CurrentStep2T 98:126 and
  EpiFlash2T 42:125. Restrict probe fitting to exactly one archived spike per trial.
- Convert MATLAB spike indices from one-based to zero-based. Read actual sample
  rates: 10 kHz for the selected current-step trials and 50 kHz for optogenetic trials.
- Port `makeInTime`, `makeFrameTime` and the raw TTL branch of `postHocExposure`.
  Use exposure **end** sample indices, rather than rising edges or an assumed
  fixed frame rate. Trim extra trailing camera triggers as the authors do.
  No missing frames needed insertion in these single-spike trials.
- Verify adjacent stored probe evaluation points are one image pixel apart.
  The [paper's methods](https://elifesciences.org/articles/56754) give pixel area
  1.03 square micrometres, so linear pitch is sqrt(1.03) um/pixel. Reports also
  retain amplitude sensitivity to pitches 1.0 and 1.03. This is a small scale
  uncertainty, not a replacement for original microscope calibration.
- Subtract the mean of the last four pre-spike probe frames, following the author
  analysis. Do not refit baseline against post-spike evaluation data.
- Measure the approximately -5 pA calibration pulse using the author's current
  windows at 10-60 vs 60-110 ms from acquisition start, and voltage windows at
  40-60 vs 90-110 ms. Fit delta-V / delta-I separately from the twitch response.
- Apply the paper's post hoc -13 mV voltage shift to baseline summaries. It cancels
  from pulse differences. Do not interpret raw somatic voltage as a spike threshold.

The archived probe tracks and spike detections are reused; videos were not
retracked. Source code is pinned and hashed in `raw_motor_sources.json`; recording
hashes, exact trial splits, frame audits and all fitted traces are in the result.

## Reproduce

From the repository root, with the two verified ZIPs under the ignored recordings
directory:

```powershell
.venv/Scripts/python.exe scripts/calibrate_raw_motor.py --out results/raw_motor_calibration_repeat
.venv/Scripts/python.exe -m unittest discover -s tests -v
```

After a fresh clone, retrieve just
[180222_F1_C1.zip](https://datadryad.org/downloads/file_stream/585425) and
[180405_F3_C1.zip](https://datadryad.org/downloads/file_stream/585433) from the
[public dataset](https://datadryad.org/dataset/doi:10.5061/dryad.76hdr7stb).
The script rejects partial or checksum-mismatched inputs. It reads named MATLAB
members directly from the archives without extracting or executing MATLAB code.

**95 offline tests pass.** New tests cover acquisition origins, MATLAB indices,
exposure edge timing, missing-frame handling, passive units and polarity, probe
scale/alignment, known-response recovery at different camera phases, and archive
corruption rejection. A repeat analysis reproduced the fitted values exactly.

## Execution boundary and next useful step

Zero neural simulation steps, no new sensory exposure and no aversive training.
No welfare conclusion follows from reading recordings or fitting algebraic curves.
Live neural attachment remains disabled. This checkpoint supplies an empirical
single-spike loaded-probe response and passive somatic targets; M3 is still incomplete.

The next useful step is mechanical-only: reproduce the experimental probe load
and map force through a measured contact lever arm to the simulated joint. Fit
that mechanical model to these recorded displacement traces, rather than turning
micrometres of probe deflection directly into joint angle. Recruiting the actual
motor unit from sensory input still needs a separately justified excitability
model and the standing neural-exposure review.
