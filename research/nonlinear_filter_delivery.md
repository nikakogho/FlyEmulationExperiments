# Nonlinear response fit: improvement with a high-bandwidth regression

The offline extension improves pooled prediction error on the reserved brighter
background by **8.4%**, but increases error on its 500 Hz stimulus by **10.4%**.
It therefore **fails the predeclared promotion gate** and is not connected to the
brain or promoted as a generally more accurate receptor model.

## Experiment and frozen choices

Sources and extraction are unchanged from [the paired-recording audit](causal_filter_delivery.md).
The candidate is a monotone static transform of the recorded light signal,
followed by the same 81-coefficient causal filter (0..80 ms at 1 ms sampling).
This is offline signal regression without recurrent cellular state, reward,
actions, body physics or a neural recipient.

Selection uses only BG0.5 (Origin DC1) 20/50 Hz recordings: raw samples 0:1200
for fitting, 1400:2000 for development validation, excluding the first 80 targets
of every block. Seven fixed transforms and five ridge penalties give 35 nonlinear
candidates; the identity baseline selects its penalty from the same five values.
No candidate is chosen using an evaluation response.

The winner is `sign(x) * log(1 + abs(x)/0.5)` with penalty 1.0. Its development
RMSE is 1.6499 mV versus the identity baseline's 2.0401 mV: **19.1% lower**. Both
choose the largest penalty offered, which does not establish a global optimum.

The protocol and selected candidate were committed and pushed as **de3095b**
before running evaluation. A separate command verifies hashes of selection,
protocol, data and fitting code before evaluating; it refuses changed inputs or
overwriting an evaluation. The audit had inspected source values and descriptive
statistics previously. The reserved endpoint is **prediction performance on
BG1.5 100/200/500 Hz**, which had not previously been evaluated. It is not a new
animal, a proven independent random seed, or an entirely unseen raw dataset.

For BG1.5, filter coefficients and intercept are refit only on its 20/50 Hz
training stimuli, using the already-frozen transform and penalty. The identity
baseline receives the same background-specific refit. Thus this evaluates
transfer of a fitting recipe, **not automatic adaptation by one unchanged model**.
No offset, gain, centering or alignment is fitted to evaluation responses.

## Results

Errors below are RMSE divided by the recorded mean waveform's temporal SD;
they are not percentages of information lost or biological fidelity.

| Reserved BG1.5 stimulus | Linear error / SD | Nonlinear error / SD | RMSE change |
|---|---:|---:|---:|
| 100 Hz | 0.3519 | 0.3156 | 10.3% lower |
| 200 Hz | 0.3211 | 0.2825 | 12.0% lower |
| 500 Hz | 0.2972 | 0.3280 | 10.4% higher |

Pooled RMSE is computed over the same 1,920 scored samples in each condition,
using absolute mV errors. It falls by **8.4%**. This statistic gives more weight
to larger-voltage responses; per-condition errors remain visible to prevent that
aggregate from hiding a regression.

All three nonlinear errors are below the frozen 0.35 absolute threshold. The
nonlinear model also beats current-input regression and shifted-training controls
by the required margins. However, acceptance also requires **no condition to get
worse than the linear baseline**. The 500 Hz result fails that criterion. The
threshold was not relaxed after observing results. These are engineering
usefulness criteria, not biological equivalence or welfare thresholds.

For the previously seen BG0.5 conditions, reported only as regression checks:

| Earlier stimulus | Linear error / SD | Nonlinear error / SD |
|---|---:|---:|
| 100 Hz | 0.4473 | 0.3753 |
| 200 Hz | 0.4038 | 0.2846 |
| 500 Hz | 0.2677 | 0.3432 |

Pooled error falls by 16.1% there, with a 28.2% regression at 500 Hz. The repeated
tradeoff supports investigating limitations of this static input compression;
it does not by itself identify the missing biological mechanism. Choosing the
linear or nonlinear model separately by test-condition results would leak the
answer into model selection, so no such mixed result is presented.

## Source-domain correction and verification

The initial v1 selection attempt stopped **before fitting** because its input
validation assumed nonnegative recorded light values. BG0.5 has small negative
source values: 8 samples at 20 Hz (minimum -0.00982) and 15 at 50 Hz (minimum
-0.04105). Their instrumental origin is unresolved. We did not clip them or infer
a photon zero point. Version 2 freezes signed extensions of the candidate
transforms so the recorded signal can be retained exactly. This mathematical
extension has no claim to negative photon counts or calibrated phototransduction.
The original protocol and failure note remain in `results/nonlinear_filter_v1/`.

**203 software tests pass.** New tests cover known nonlinear-system recovery on
an independent synthetic sequence, monotonicity and signed values, invalid-input
rejection, future-input invariance and non-overlapping blocks. A whitelist-backed
data mapping makes selection fail if it requests any non-development condition.

`scripts/check_nonlinear_evidence.py` independently uses an explicit log formula
and convolution, checks source/artifact hashes, verifies the selected development
minimum, recomputes every condition metric and acceptance gate, and matches saved
predictions within **8.88e-15 mV**. Its consistency check passes; model acceptance
remains failed. The generated comparison plot was visually inspected.

No fly, connectome, neural adaptation or welfare protocol was run. These checks
do not establish absence of suffering. Existing neural stops and standing
protocol requirements remain unchanged. Population traces at BG1.5 are excluded
because overlap with the primary cell remains unresolved.

## Reproduction and next bounded experiment

Use the audited, hash-checked local arrays from `results/origin_audit_v1/` and a
new output directory. Selection and evaluation are deliberately separate:

```powershell
.venv/Scripts/python.exe -m unittest discover -s tests -v
.venv/Scripts/python.exe scripts/benchmark_nonlinear_filter.py select --out results/nonlinear_filter_repeat
.venv/Scripts/python.exe scripts/benchmark_nonlinear_filter.py evaluate --out results/nonlinear_filter_repeat
.venv/Scripts/python.exe scripts/check_nonlinear_evidence.py --path results/nonlinear_filter_repeat
.venv/Scripts/python.exe scripts/plot_nonlinear_filter.py --path results/nonlinear_filter_repeat
```

The next tractable hypothesis is a regularized two-path filter that retains a
linear input path alongside the compressed path, selected on development data.
It might preserve fast changes better, but the present results do not establish
that it will. Reserve another condition before testing that hypothesis; the
BG1.5 results here are now seen and cannot be reused as fresh confirmation.
Absolute photon calibration, illumination adaptation, R7/R8 dynamics, neural
integration and learned 3D behavior remain separate evidence gaps.
