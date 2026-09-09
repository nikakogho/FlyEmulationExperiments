# Comparing our polarity test with the authors' analysis

Our earlier moving-edge test was not the authors' flash-response measurement.
However, applying their actual flash analysis to the same default checkpoint
still produces a negative T4d index. Thus the mismatch is not solely an artifact
of our custom edge-peak metric. It is a property of this fitted checkpoint under
these stimuli, rather than evidence that FlyVis as a whole cannot be used.

## What differs

| Aspect | Our first check | Authors' implemented analysis |
|---|---|---|
| Polarity stimulus | Moving ON/OFF edges, four directions, one speed | Stationary flash, radius-6 disk in the figure analysis |
| Time course | 1 s pre, edge motion, 1 s post | 1 s gray, 1 s flash, 1 s gray |
| Peak processing | Subtract pre-stimulus mean, keep positive peaks | Select -dt through 1 s; add absolute minimum across time and polarity, then take peaks |
| Polarity statistic | Largest expected-polarity peak exceeds largest other-polarity peak | FRI = (ON peak - OFF peak)/(ON peak + OFF peak + epsilon) |
| Model scope | One default checkpoint, all eight types must pass | Ensemble analysis; Fig. 2 notebook prints ten task-ranked models |
| Direction statistic | Preferred-versus-opposite contrast at four directions | Vector sum across angles, normalized across both intensities; default dataset also includes multiple speeds |

The earlier direction checks remain useful engineering checks, but their
indices are not numerical reproductions of the authors' DSI values.

Primary implementation references at the pinned commit:
[flash analysis](https://github.com/TuragaLab/flyvis/blob/92b3845cc426dd309a1a0e1b3890156c42e14021/flyvis/analysis/flash_responses.py),
[stimulus configuration](https://github.com/TuragaLab/flyvis/blob/92b3845cc426dd309a1a0e1b3890156c42e14021/flyvis/analysis/stimulus_responses.py),
[Fig. 2 notebook transcript](https://github.com/TuragaLab/flyvis/blob/92b3845cc426dd309a1a0e1b3890156c42e14021/docs/docs/examples/figure_02_simple_stimuli_responses.md).

## Exact default-checkpoint test

`scripts/compare_author_polarity.py` calls the upstream `flash_responses` and
`flash_response_index` functions without altering their numerical analysis.
It uses the same storage-only Windows compatibility fix as the earlier run.
An independent NumPy calculation matched the returned FRI values within
1e-7. Both radius 6 and full-field flashes were tested; the latter is a
diagnostic, not a replacement for the figure's radius-6 choice.

For checkpoint 000, radius-6 T4d FRI is **-0.31194**; full-field FRI is
**-0.31202**. The other seven T4/T5 types have their expected signs in both
conditions. The default T4d's OFF preference therefore survives the change
to the authors' stimulus and metric.

## Fixed ensemble comparison

We use exactly the ten checkpoint identifiers printed by the authors' Fig. 2
notebook: 000, 001, 002, 003, 004, 005, 007, 009, 006, 013. Their archived list
is used directly; we did not pick checkpoints for agreement with our test.
Every model runs the upstream flash pipeline at 200 Hz. Raw central-cell
responses and all model results are retained in `results/author_ensemble/`.
This checks model variability with the same analysis, not a numerical
reproduction of every figure panel or the underlying biological recordings.

All ten models completed. Results for the paper's radius-6 stimulus:

| Cell | Ensemble median FRI | Models with expected sign |
|---|---:|---:|
| T4a | +0.3882 | 9/10 |
| T4b | +0.3411 | 10/10 |
| T4c | +0.3662 | 10/10 |
| T4d | **+0.3748** | **9/10** |
| T5a | -0.1536 | 6/10 |
| T5b | -0.0950 | 8/10 |
| T5c | -0.0636 | 9/10 |
| T5d | -0.1987 | 9/10 |

All eight ensemble medians have the expected polarity sign. The default
checkpoint is the sole T4d sign exception in this fixed set. Other types also
have individual-model exceptions, especially T5a. The original failed gate
remains a valid warning about that checkpoint, but should not be presented as
a failure of the ensemble-level biological claim.

The practical recommendation is to retain uncertainty across models and
validate intended pathways on separate stimuli before integration. Do not
silently switch to a passing checkpoint and claim the discrepancy is fixed.
This comparison supports continuing the visual-model approach; it neither
establishes better learning nor supplies the missing anatomical connection
to our learning circuit.

## Reproduce

```powershell
.venv-vision/Scripts/python.exe scripts/compare_author_polarity.py
.venv-vision/Scripts/python.exe scripts/compare_author_ensemble.py
.venv/Scripts/python.exe scripts/plot_author_comparison.py
```

The first two scripts refuse to overwrite existing result directories; archive
those directories before a fresh run. The ensemble script saves partial
progress with `complete: false` and marks completion only after all ten models.
The plot requires completion. Exit 0 means the comparison executed successfully,
not that every biological sign agrees. No checkpoint was retrained, no motor
controller or learning circuit was connected, and no whole-brain model ran.
