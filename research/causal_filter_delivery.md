# Paired receptor recordings and first causal response fit

The user-supplied Origin projects resolve the missing light-input waveform
blocker. Both files match Dryad's published MD5s and have pinned SHA256 hashes in
`results/origin_audit_v1/audit.json`. All **800,000** primary-cell voltage samples
match the separately published Excel exports to **4.97e-14 mV**. This is an audit
of source agreement, not measurement precision. No new neural model was run.

## What was recovered and checked

The two sources are [Figure 1 and its population supplement in Dryad](https://datadryad.org/dataset/doi:10.5061/dryad.12751),
associated with [Juusola et al., 2017, Figure 1](https://elifesciences.org/articles/26117#fig1).
Each project contains 25 worksheets and one graph. The four `WNstimDC*` sheets
contain 20 light-input waveforms: 20/50/100/200/500 Hz bandwidths at four
backgrounds. Each waveform has 2,000 observed samples at 1 ms spacing.

The importer verifies every stimulus/response time axis, stored graph references,
condition names, means, sample SDs and finite values. Both projects contain
identical stimulus columns. Origin's missing-value sentinel is removed only from
trailing padding; a missing value within an observation fails the audit. There is
no padding, invented stimulus, interpolation or formula execution.

The first positional voltage comparison failed because worksheet column order
differs from numerical trial order. Reading columns by `n1` through `n20` resolves
the discrepancy and independently matches all Excel samples. Source files were
not changed. Reader tests now cover that exact failure mode.

The supplement has 16, 7, 8 and 4 cell-mean traces per condition at paper
backgrounds 0, 0.5, 1 and 1.5 respectively: 175 cell-condition records, **not 175
independent animals**. At BG0.5, supplement `n1` exactly duplicates the primary
cell's 20-trial mean in all five conditions. It is excluded from transfer testing.
Other backgrounds' identities and preprocessing differences are not resolved and
are not used in this fit. The 80,000-sample `responseReps` records are preserved in
the raw exports but excluded from this benchmark.

Pairing is supported by worksheet names, common 1..2000 ms axes, graph curve
references and the paper's Figure 1 captions. We apply no fitted time shift.
Independent instrument latency and sub-ms timing are not established. Stimulus
values remain the stored source units; they are not calibrated absorbed photons.
Published relative-voltage preprocessing is retained, including any use of
whole-record statistics by the authors. No new normalization uses test responses.

## Frozen benchmark and outcome

`research/calibration/causal_filter_protocol.json` was written before fitting.
It specifies an engineering **causal linear filter with lags 0..80 ms**, trained
only on the primary cell's BG0.5 20 and 50 Hz stimulus/mean-response pairs. It is
ordinary matrix regression over archived numbers, with no recurrent cellular
state, circuit, action, reward or learning agent instantiated.

Regularization is selected on blocked development data: raw samples 0:1200 for
fitting, 1400:2000 for validation, discarding each block's first 80 targets so lag
windows cannot cross block boundaries. Five fixed penalties were tried; 1.0 won.
The model is then refit on both training conditions, and evaluated on the held-out
100/200/500 Hz conditions after the same 80-sample history exclusion.

The controls are a current-input linear model and a causal filter fitted to
stimuli shifted by 1,000 samples relative to training responses. Prediction uses
only the current and past stimulus, never the recorded test voltage. The shifted
training control uses the same selected penalty. No condition-specific output
offset, gain, time shift or fit is added at evaluation.

| Held-out bandwidth | FIR RMSE (mV) | FIR RMSE / waveform SD | Current-input error / SD | Shifted-training error / SD | Accuracy gate |
|---|---:|---:|---:|---:|---|
| 100 Hz | 1.5652 | 0.4473 | 1.1095 | 1.2256 | Fail |
| 200 Hz | 0.8366 | 0.4038 | 1.2365 | 1.2359 | Fail |
| 500 Hz | 0.3906 | 0.2677 | 1.5172 | 1.2588 | Pass |

The fixed same-cell gate required normalized RMSE <=0.35 and at least 20% lower
RMSE than each control in **every** condition. Improvement over the current-input
control is 59.7%, 67.3% and 82.4%. The first two conditions miss the absolute error
target, so **overall model acceptance fails**. No threshold was changed and no
second model was tuned on these test results. The 0.35 threshold is an engineering
usefulness choice, not a biological equivalence criterion.

Across the six other cell columns in each of the three test conditions, median
normalized error is **0.4793**, passing the declared median <=0.5 transfer target.
Individual errors span **0.3083-1.0255**: transfer is uneven, and a median pass does
not imply reliable prediction for every cell. These are 18 cell-condition
observations with dependence; no independent-animal significance claim is made.
Bandwidth holdout also does not establish independent random stimulus seeds.

The plot is `results/causal_filter_v1/comparison.png`. Predictions and raw exports
are ignored local artifacts; the protocol, all numerical metrics, fitted 81
coefficients, source hashes and implementation are tracked.

## Verification, welfare and next step

**195 software tests pass**, including recovery of a known causal filter on a
new synthetic sequence, future-input invariance, non-overlapping development
windows, a shifted-input negative control, missing-data rejection and name-based
trial ordering. A separate evidence checker predicts with convolution instead of
the fitting implementation's design matrix; maximum disagreement is **5.33e-15
mV**. It verifies hashes and recomputes the acceptance decision from saved arrays.
That check passes; the biological-response fit's acceptance still fails.

This checkpoint only parses recorded data and performs offline numerical
regression. No fly brain, connectome, FlyVis, neural adaptation, body or
reinforcement protocol runs. It supplies no welfare assessment or proof of
absence of suffering. Standing stops and the requirements in `milestones.md`
remain in force for any future neural protocol.

The tractable next improvement is an offline comparison of a small static
nonlinearity plus causal filter against this linear baseline, with selection
restricted to development data. These now-seen test conditions can serve as
regression checks, not a fresh untouched test. Reserve another documented
cell/condition split before choosing the next model. Investigate gain differences
and source preprocessing rather than assuming a poor cross-cell fit is corrected
by adding more neural complexity. Absolute scene-to-photon calibration, R7/R8
dynamics, adaptation across illumination levels, connectome integration and
learned behavior remain separate unvalidated steps.

## Reproduction

Leave the downloads intact. Copy the original user downloads to
`data/receptor_calibration/figure1.opj` and `figure1_supp1.opj`. The audit checks
both expected hashes. The Excel source files are reproducible via the preceding
voltage-audit script. No Origin license is needed.

The reader is [python-liborigin2](https://github.com/Saluev/python-liborigin2),
pinned to `f19e74517059769f9525b477ab934b6f9b1602d5`. Its read-only parser exports
stored fields without evaluating Origin commands, macros or formulas. It runs in
a network-disabled Docker container with read-only inputs/root and a writable
output directory. The project simulation environment was not modified.

```powershell
git clone https://github.com/Saluev/python-liborigin2 upstream/python-liborigin2
git -C upstream/python-liborigin2 checkout f19e74517059769f9525b477ab934b6f9b1602d5
docker build -t fly-origin-reader:local -f scripts/origin_reader.Dockerfile upstream/python-liborigin2
New-Item -ItemType Directory results/origin_extraction_repeat
$repoPath = (Get-Location).Path
docker run --rm --network none --cpus 2 --memory 2g --read-only --tmpfs /tmp:rw,size=256m --workdir /tmp --mount "type=bind,source=$repoPath/data/receptor_calibration,target=/inputs,readonly" --mount "type=bind,source=$repoPath/results/origin_extraction_repeat,target=/output" --mount "type=bind,source=$repoPath/scripts/export_origin_project.py,target=/export.py,readonly" fly-origin-reader:local python /export.py /inputs/figure1.opj /output/figure1.json.gz
docker run --rm --network none --cpus 2 --memory 2g --read-only --tmpfs /tmp:rw,size=256m --workdir /tmp --mount "type=bind,source=$repoPath/data/receptor_calibration,target=/inputs,readonly" --mount "type=bind,source=$repoPath/results/origin_extraction_repeat,target=/output" --mount "type=bind,source=$repoPath/scripts/export_origin_project.py,target=/export.py,readonly" fly-origin-reader:local python /export.py /inputs/figure1_supp1.opj /output/figure1_supp1.json.gz
```

Run the audit with a Python containing NumPy and openpyxl (the bundled runtime was
used here); run the benchmark, checker, plot and unit suite with project Python:

```powershell
python scripts/audit_origin_receptors.py --exports results/origin_extraction_repeat --out results/origin_audit_repeat
.venv/Scripts/python.exe scripts/benchmark_causal_filter.py --data results/origin_audit_repeat --out results/causal_filter_repeat
.venv/Scripts/python.exe scripts/check_causal_filter_evidence.py --data results/origin_audit_repeat --path results/causal_filter_repeat
.venv/Scripts/python.exe scripts/plot_causal_filter.py --path results/causal_filter_repeat
.venv/Scripts/python.exe -m unittest discover -s tests -v
```

The reader image used Python 3.12.13, Cython 0.29.37, setuptools 75.8.2,
g++ `4:14.2.0-1`, libboost-dev `1.83.0.2+b2`; image ID
`sha256:6d210af6161fedfe7d2ce74db5bf2d455809aa0f70d756ecbae79ae465880ac7`.
Base image, parser revision and Python build dependencies are pinned in source;
APT packages are resolved at build time, with the observed versions recorded here.
An initial Cython 3 build failed on the old wrapper's Python 2 print syntax;
Cython 0.29.37 built it successfully without modifying upstream. No numerical
source data or failed scientific threshold was changed to repair that tool issue.
