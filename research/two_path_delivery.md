# Two-path response filter: reserved test failed

The proposed combination of linear and compressed input paths was implemented,
selected on development recordings, and evaluated after freezing its settings.
**Reserved BG1 pooled error increased by 11.2% versus the linear baseline.** All
three individual conditions worsened. The candidate is rejected; no neural
integration, automatic fallback selection, or threshold relaxation followed.

## Protocol and separation

The model concatenates two sets of 81 causal features: the original source signal
at lags 0..80 ms, and `sign(x)*log1p(abs(x)/0.5)` at the same lags. There are 162
coefficients plus an intercept, fitted jointly using the existing training-only
ridge centering and scaling. This is a mathematical hypothesis, not an identified
two-path biological circuit. Signed source values are preserved unchanged.

Each of the linear, compressed-only and combined models independently chooses
one of five fixed ridge penalties using only BG0.5 20/50 Hz development data.
Fit block: raw samples 0:1200; validation block: 1400:2000. Each block independently
loses its first 80 targets, preventing cross-block lag leakage. No evaluation
responses enter model selection. The combined penalty is 0.1; the two baselines
select 1.0. Combined development RMSE is 1.6350 mV, versus 2.0401 linear and
1.6499 compressed-only: about 19.9% better than linear, but only 0.9% better than
compressed-only. Greater complexity bought little extra development improvement.

Selection, source and protocol were committed and pushed as **efe66a1** before
evaluation. The evaluation command checks those hashes and refuses overwrites.
The new endpoint was prediction performance on **BG1 (Origin DC2) 100/200/500 Hz**.
Raw source values and audit statistics had previously been inspected, but those
prediction endpoints had not been evaluated. All primary recordings are from the
same cell; independent animals and independent random stimulus seeds are not
established.

Each model is refit only on the evaluation background's 20/50 Hz training
recordings using frozen penalties. This tests a fitting recipe after
background-specific calibration, not autonomous adaptation by an unchanged model.
No evaluation-response gain, offset, time alignment or normalization is fitted.
BG0.5 and BG1.5 are reported only as previously seen regression checks. Population
data are excluded because duplicate-cell mappings outside BG0.5 remain unresolved.

## Reserved result

| BG1 stimulus | Linear RMSE / SD | Compressed-only RMSE / SD | Combined RMSE / SD |
|---|---:|---:|---:|
| 100 Hz | 0.3591 | 0.3081 | 0.3708 |
| 200 Hz | 0.3524 | 0.2915 | 0.4087 |
| 500 Hz | 0.3418 | 0.3952 | 0.5179 |

Each metric compares 1,920 predicted samples with the published 20-trial mean.
Normalized RMSE divides absolute voltage error by that mean waveform's temporal
SD. It is not percentage information loss or a biological fidelity percentage.
Pooled RMSE uses all equal-length conditions in mV, so high-amplitude responses
contribute more. Individual conditions remain visible alongside the aggregate.

The predeclared acceptance checks required development and reserved pooled error
at least 5% below linear, no reserved condition worse than linear, every reserved
normalized error <=0.35, and at least 20% improvement over current-input and
shifted-training controls. Reserved pooled improvement, non-regression and
absolute accuracy all **fail**; the two control comparisons pass. Overall status
is **failed**. The compressed-only results are diagnostic comparisons, not a
replacement selected after looking at this test.

On the old BG0.5 regression conditions, combined pooled error is 16.1% below
linear; on old BG1.5 it is 12.2% above linear. The 500 Hz regression remains:
combined normalized errors are 0.3375 and 0.4160 versus linear 0.2677 and 0.2972.
These results do not identify a biological cause, but they reject this particular
recipe as a general improvement. No extra candidate was tuned after evaluation.

## Verification and welfare boundary

**208 software tests pass**, including known two-path system recovery on a new
synthetic sequence, causal feature ordering, future-input invariance, block
boundaries, invalid inputs, and selection with a mapping containing only allowed
development keys. Existing tests remain passing.

The independent checker directly evaluates the signed logarithm and convolves
each input path separately, rather than using the fitting code's design matrix.
It verifies all saved predictions, metrics, gates, source and artifact hashes,
and the development selection minima. Maximum prediction disagreement is
**8.88e-15 mV**. The evidence-consistency check passes while model acceptance
fails. The generated comparison plot was visually inspected.

Only matrix operations on existing recordings ran. No neural recipient,
connectome, recurrent cellular model, body, valence or reward system was advanced.
This does not constitute a welfare assessment or proof of absence of suffering.
Standing neural stops and protocol requirements remain unchanged.

## Reproduce and change direction

With the hash-checked arrays from `results/origin_audit_v1`, use a new output path:

```powershell
.venv/Scripts/python.exe -m unittest discover -s tests -v
.venv/Scripts/python.exe scripts/benchmark_two_path.py select --out results/two_path_repeat
.venv/Scripts/python.exe scripts/benchmark_two_path.py evaluate --out results/two_path_repeat
.venv/Scripts/python.exe scripts/check_two_path_evidence.py --path results/two_path_repeat
```

Source, compact reports, coefficients and protocols are tracked; numerical arrays
and the generated `comparison.png` are ignored local artifacts.

Do not continue consuming backgrounds as one-off test sets for increasingly
flexible filters selected on the same two development conditions. The next useful
bounded step is an offline audit of population cell identifiers and duplicate
records, followed by a protocol that holds out whole identifiable cells and
tests several illumination levels. Distinguish archived figure preprocessing
from raw recording differences before claiming a transfer failure is mechanistic.
The present results should become development/regression evidence, not be reused
as fresh confirmation. A stronger sensory-data benchmark remains separate from
absolute photon calibration, R7/R8 response models, brain integration and learning.
