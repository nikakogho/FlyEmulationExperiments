# Spectral coverage and temporal calibration audit

2026-09-21. Completed a separate, opt-in spectral reconstruction and compared it
with the archived 3D sensory scene. No connectome, visual neural network,
photoreceptor dynamical model or physical integration was run.

## What changed

The original receptor data ended at 550 nm. We extracted the second measurement
block from Sharkey et al.'s source workbook: **450-700 nm for Rh1 and Rh6**.
The new `CalibratedSpectralReceptors` joins those bands to the existing short-wave
measurements. Its five-receptor interface still rejects wavelengths above 550 nm:
the source does not supply those tails for Rh3, Rh4 and Rh5. A caller must explicitly
select Rh1/Rh6 to use the extended range. Unknown responses never become zeros.

The raw means, sample SDs, wavelength grids, workbook cells, URL and SHA256 are
tracked in `calibration/sharkey2020_bands.json`. The source workbook stays unchanged
and excluded from Git. The legacy data, renderer and archived experiments remain
unchanged. This candidate does not silently replace their spectral model.

## Reconstruction and its limits

Source: [Sharkey et al. 2020](https://www.nature.com/articles/s41598-020-74742-1),
Supplementary Data 1, `Sheet 1!D3:N50` and `Sheet 1!O3:S53`, and Methods, Data
analysis. These are red-eye single-opsin-rescue ERG measurements, six animals per
band. They are not isolated opsin absorbance or absolute single-cell gains.

The paper specifies a **0.5777** multiplier for the long-wave Rh1 curve. For Rh6,
our explicit reconstruction fits one positive multiplicative factor through the
origin across the 21 overlapping wavelengths: **1.3611468**. The paper describes
overlap alignment but does not uniquely specify that estimator; our implementation
is therefore an approximation, not a claim of exact reproduction of their code.

At overlap wavelengths we average the aligned means and pool the sample SDs,
including the difference between group means. Each joined mean curve is divided
by its own full-range maximum. Normalized SD is descriptive spread; it excludes
scale-estimation and peak-normalization uncertainty and is not a confidence band.

Rh6's reconstructed peak is at **600 nm** in these wide-field ERG measurements.
This does not establish the same peak for every natural scene or retinal location;
screening pigment and illumination geometry matter. Our uniform-radiance scene
still lacks wavelength-dependent light transport and full eye optics.

## Tests and comparison

- **181 tests pass**, including seven new tests for source anchors, full Rh6 peak,
  missing-channel rejection, pooled uncertainty, linearity, nonuniform quadrature,
  and exact preservation of short-band-only receptor curves.
- Re-rendered nine unchanged body poses from the original three-second recording.
  The old renderer reproduced every selected archived retinal array exactly.
- The candidate preserved R7 and pale R8 values exactly. Only Rh1 and yellow R8
  changed. Across these poses the mean outer-channel proxy changed from 0.04742 to
  0.04794; mixed R8 changed from 0.04800 to 0.03588. **These are changes in normalized
  proxy units, not evidence of lower neural activation, better behavior or welfare.**
- Exploratory alternating-wavelength check: fit Rh6 scale on 11 overlap wavelengths
  and evaluate the other 10. Alignment reduced RMSE from 0.48619 to 0.05980 in source
  amplitude units. The wavelengths share source animals; this is an alignment
  diagnostic, not independent physiological validation or a preregistered gate.
- A first comparison failed exact equality by 6.94e-18 because of matrix layout
  and floating-point reduction order. We fixed layout to match the legacy code,
  retained exact equality, and preserved the failure in `spectral_calibration_v1`.

Evidence: `results/spectral_calibration_v2/comparison.json`, `comparison.png`,
and `results/spectral_calibration_tests.log`. Generated arrays/images remain local.

## Temporal dynamics: audited, not implemented or validated

[Juusola and Hardie 2001](https://pmc.ncbi.nlm.nih.gov/articles/PMC2232468/) measured
R1-R6 voltage responses at 25 C with a green point-source LED. Their Fig. 6 and text
report approximate bright/dim delays of 10/20 ms and peaks of 20/40 ms. A membrane
RC time constant alone cannot describe the full light response. The dependence on
background illumination also prevents using one fixed kernel as general adaptation.

We recovered the paper XML and the complete Europe PMC supplementary archive.
That archive contains raster figures, not numeric response traces. Source URLs and
hashes are in `calibration/source_provenance.json`. We also inspected the public
2017 microsaccadic-sampling repository at revision
`a4453f7e47abf2ea2a924c376d4c1c157c6011e2`; its tree supplied no raw voltage dataset.
A further lead, [Hue selectivity from recurrent circuitry](https://pmc.ncbi.nlm.nih.gov/articles/PMC11537989/),
links raw calcium traces at Zenodo 10720630. Calcium is a different measurement and
cannot be substituted directly for a photoreceptor voltage kernel.

The saved scene has a 10 ms interval: only one sample per bright-condition delay
and two per bright-condition peak. It can test static optics but is insufficient
for a strong millisecond response-timing validation. Its relative radiance also
does not specify effective absorbed photons per second, so it cannot determine
which published adaptation condition applies. Upsampling would fix neither gap.

The next executable temporal checkpoint is:

1. Obtain numerical voltage/stimulus traces with temperature and adapting light
   specified, or explicitly digitize published curves as approximate development
   data. Preserve pixel/axis uncertainty; do not call digitized fits raw data.
2. Reserve a separate cell/condition for prediction. An interleaved subset of one
   plotted fitted curve is insufficient for independent physiological validation.
3. Fit the smallest supported causal kernel to the development condition only;
   compare latency, peak time, waveform and frequency response on the reserved data.
   R1-R6 evidence does not calibrate R7/R8. Absolute scene gain remains a separate gate.
4. Acquire a new short mechanical/optical fixture at 1 ms, then 0.5 ms to measure
   numerical convergence. This is an engineering sampling choice, not a claim that
   a fly samples its world at a fixed 1 kHz. Do not interpolate the old 100 Hz tape
   and present it as new optical evidence.
5. Only after those checks consider a new bounded neural protocol under
   `milestones.md`. No old efficacy failure or welfare stop is reopened here.

## Reproduce

The source JSON is committed, so loading the new model needs no workbook tooling.
To reconstruct it from the pinned workbook, use a Python with openpyxl and NumPy:

```powershell
python scripts/extract_spectral_bands.py
.venv/Scripts/python.exe -m unittest discover -s tests -v
.venv/Scripts/python.exe scripts/compare_spectral_calibration.py --out results/spectral_calibration_repeat
```

The comparison requires the excluded original `sensory_scene_v2` arrays and the
pinned FlyGym installation; recreate the original recording using its delivery
instructions if needed. Output folders must be new to avoid overwriting evidence.

## Welfare boundary

All new operations were workbook extraction, source inspection, static numerical
integration and re-rendering archived poses. **Zero neural steps.** No claim about
absence of suffering follows from these apparatus checks. No reward, deprivation,
threat, adverse learning or restored stopped neural state was introduced.
