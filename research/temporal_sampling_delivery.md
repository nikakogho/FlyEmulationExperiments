# Numerical receptor traces and high-rate 3D optical acquisition

Follow-up: the user supplied both Origin files. The missing-input blocker is
resolved; see [the extraction audit and first causal fit](causal_filter_delivery.md).
The remainder of this document preserves the earlier checkpoint as recorded.

2026-09-23. New numerical data and an optical timing fixture are available.
No temporal photoreceptor model was fitted or executed. No connectome ran.

## Recovered measurements

The 2017 paper has directly downloadable Excel source data, separate from its
Dryad Origin projects. We retrieved [Figure 1 source data 1-4](https://elifesciences.org/articles/26117#fig1),
with 20 repeated voltage responses to each of 20 stimulus conditions: **400 traces,
800,000 voltage samples**, 1 ms intervals over 2 seconds. These are repeated
measurements of **one R1-R6 cell**, not 400 animals. The paper identifies 25 C for
these experiments. Figure 3 source data are simulated responses and were excluded.

The read-only importer checks pinned workbook hashes, all time axes, column labels,
finite values, and the provided means/sample SDs. Recomputed means agree to
5.33e-14 mV and SDs to 1.25e-12 mV. Each source sheet's B2:X2001 is accounted for.
Data files 3 and 4 reuse BG05 worksheet names despite publisher captions specifying
BG1 and BG1.5; the importer preserves both and uses the caption mapping explicitly.
Negative values are recorded voltage-response shifts, not evidence of negative
valence or calibrated absolute membrane potentials.

The four source URLs, SHA256 hashes and per-condition numerical checks are in
`results/voltage_sampling_v2/audit.json`. Downloaded workbooks and extracted arrays
are excluded from Git. `scripts/audit_voltage_sampling.py --download` recovers them
from pinned publisher URLs when missing, with a hash check before saving.

## A benchmark we can perform now

We subsampled each published mean voltage waveform and reconstructed it with
linear interpolation, evaluating only times covered by the retained samples.
This models instantaneous sampling; no antialias filter was applied.

| Acquisition interval | Sampling rate | Reconstruction RMSE / temporal SD, across 20 conditions |
|---|---:|---:|
| 10 ms | 100 Hz | 5.46-23.94% |
| 5 ms | 200 Hz | 1.54-10.06% |
| 2 ms | 500 Hz | 0.34-3.54% |
| 1 ms | 1 kHz | 0 by construction (published reference) |

These percentages describe waveform distortion, not lost bits of information,
biological prediction accuracy or percentages of vision. Source observations at
1 kHz cannot validate faster biological dynamics. We did not train or select a
receptor model on these results. Repeated-trial noise comparisons are also reported
but do not constitute independent cell validation.

## Fresh 3D optical recording

`scripts/record_optical_timing.py` independently renders the actual two spectral
eye cameras at 10 ms, 1 ms and 0.5 ms intervals. It uses the archived resting body
pose and the existing scene. Body state stays fixed; the new optical clock controls
a declared radiance pattern, rather than advancing the physical clock. It is a
static-pose optical instrument test, not a high-rate walking/body-sense recording.

The 100 ms fixture scales all surface/sky spectra by
`1 + .15 sin(2 pi 20 t) + .05 sin(2 pi 80 t)`. Its bounds are 0.8-1.2 times the
existing scene's relative radiance. This is a synthetic acquisition test with no
neural recipient, not a proposed visual exposure for the fly model. It retains the
legacy 315-550 nm static spectral proxy to isolate the timing change.

Numerical acceptance criteria were written in
`calibration/optical_timing_protocol.json` before running:

- Samples at shared timestamps must agree exactly.
- Full-retina linearity relative error must be below 1e-10.
- The 1 ms reconstruction must have normalized error below 3% against the 0.5 ms
  recording and lower error than the 10 ms recording.
- Physical state must remain unchanged; neural and physics steps must be zero.

All passed. **313 fresh eye-frame pairs** were rendered. Shared frames agreed
exactly; maximum linearity error was 1.22e-14. Normalized reconstruction error was
**0.7149% at 1 ms**, versus **52.8753% at 10 ms**. This verifies optical acquisition
for this particular pattern, not general convergence of retinal motion, physiology
or a whole walking scene. Raw arrays and the plotted comparison are local under
`results/optical_timing_v1/`; compact checks are tracked in Git.

## Remaining blocker and useful human download

The recovered Figure 1 Excel columns contain timestamps, voltage trials, mean and
SD, **but no matching light-input waveform**. The published stochastic stimulus
cannot be reconstructed from bandwidth and average brightness alone. Fitting a
causal light-to-voltage response without that waveform would be underdetermined.

The [Dryad archive](https://datadryad.org/dataset/doi:10.5061/dryad.12751) contains
original Origin projects and population data. Direct file requests returned 403;
the public metadata API worked but its download endpoint returned 401. Attempts
through the normal browser download links produced no verified local artifact.
No account, credentials or private browser storage were accessed. These two files
are the most useful next candidates; their inclusion of the required paired stimuli
still needs to be verified after extraction:

1. Open the Dryad page and expand **Aug 28, 2018 version files**.
2. Download **Figure 1 (all responses to stimuli).opj** (17.51 MB).
3. Download **Figure 1-Fig Supl 1 (data from all cells).opj** (20.65 MB).
4. Save both in `C:/Users/nikak/source/repos/FlyEmulationExperiments/data/receptor_calibration/`.
   Their original filenames are fine; no Origin license is requested at this stage.

Once available, inspect the numerical column/graph mappings, compare duplicate
voltage traces against the audited Excel exports, and identify exact input timing.
Reserve a different cell or stimulus condition before fitting a small causal
kernel. Scene-to-absorbed-photon calibration and R7/R8 dynamics remain separate
problems; these data do not solve them. No author email was sent.

## Reproduction and checks

Use bundled Python with openpyxl and NumPy for extraction, then the project Python
for plots and FlyGym. Output directories must be new:

```powershell
python scripts/audit_voltage_sampling.py --download --out results/voltage_sampling_repeat
.venv/Scripts/python.exe scripts/plot_voltage_sampling.py --path results/voltage_sampling_repeat
.venv/Scripts/python.exe scripts/record_optical_timing.py --out results/optical_timing_repeat
.venv/Scripts/python.exe -m unittest discover -s tests -v
```

**186 tests passed**, including new endpoint, aliasing and invalid-input tests.
An initial plotting attempt failed because bundled Python lacks matplotlib;
the numerical audit had completed. Extraction and plotting now use separate
entry points/environments. The initial report and failure are preserved in
`voltage_sampling_v1`. No scientific threshold changed.

All work was analysis of existing recordings and optical rendering. A quiet
mechanical/optical test does not establish absence of suffering; the project's
standing welfare constraints and previous neural stops remain in force.
