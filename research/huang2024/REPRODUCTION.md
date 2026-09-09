# Huang–Luo memory model: reproduction status

2026-09-08. **Software reference reproduced; published-figure gate unresolved.**
Spiking integration and embodied transfer remain gated. No learning-enhancement
or improved biological fidelity claim is justified yet.

## What ran

The Python port in `flyplasticity/huang2024.py` implements the authors' released
recurrent model and uses their full-precision parameters without refitting.
Both two- and three-module parameter sets load. The Figure 5c evaluation uses
all 10,000 deposited parameter samples, not fresh draws or the fitted point
estimate substituted for the sample median. This computation takes under a
second on CPU locally; GPU use is unnecessary for this reduced model.

Fourteen software tests pass. Most importantly, the port reproduces **144
numeric values stored in native MATLAB figures** from the author's repository:
6 neuron types × 2 odors × 6 imaging times × 2 valence conditions. The native
figures use the fitting script's protocol, which differs from the Figure 5c
example's timing. Both protocols are explicit and separately tested. The
attractive-condition maximum error was 7.11e-15 Hz; the test requires 1e-10 Hz
for both conditions. MATLAB itself was not installed or executed locally.

Other tests cover parameter placement against Supplementary Table 3, exact
imaging times, dopamine activation versus suppression, blocked-dopamine and
frozen-weight controls, odor permutation, batch/single equivalence, MBON bounds,
unchanged input parameters and decay intervals crossing the 3-hour switch.
An independent direct solution of the neural graph agrees with the released
iterative solver under varied inputs and saturation.

## The failed gate is retained

Before executing the model, `validation_plan.md` specified that all 48 published
Figure 5c median values must agree within 0.05 Hz. The result is **21/48**,
RMSE **0.184599 Hz**, maximum absolute error **0.44 Hz**. This threshold is an
engineering reproduction criterion, not a test of biological significance.
The failure does not refute the paper's biology, but prevents an exact figure
reproduction claim.

The saved comparison has the published model values and the port's model values.
Experimental animal means and SEMs are retained separately in `model_outputs.npz`.
Agreement with a model's published curves is not independent validation against
animals, and matching training data does not establish held-out predictive accuracy.

## What the audit resolved

- The public MATLAB implementation caps the alpha2 MBON's evoked rate at 8.9 Hz.
  Published source-data values plateau at 8.46 Hz. Their 0.44 Hz difference is
  directly observable. The repository's available history retains 8.9.
- A second parameter archive in the fitting-results directory has the same
  fitted point parameters but different Monte Carlo samples. Testing this
  archive did not reconcile the published medians.
- Post-hoc diagnostics separately tried the alternate archive and a ceiling of
  8.46 inferred from source-data saturation. Neither combination passed the
  original gate. These diagnostic settings were not adopted or labeled as
  independent confirmation. See `provenance_diagnostics.json`.
- The released code decays **learned deviations** toward initial weights.
  Appendix Eq. 5.8 instead shows total weights decaying toward zero. This is
  a material documentation/implementation distinction, not a PDF parsing error
  (the equation was visually checked).
- Code applies adaptation and recovery sequentially even during odor, scales
  anti-Hebbian coefficients by bout duration / 90 seconds, and decays plasticity
  during every bout. A direct transcription of the abbreviated appendix would
  therefore not reproduce the released implementation.
- The three-hour switch is controlled by time since the last session named
  `training`. That is a protocol-aware experimental approximation, not a
  biological online consolidation mechanism. It must not be copied unchanged
  into an autonomous learner.
- KC-to-MBON weights here are **effective signed interactions**, summarizing
  direct and indirect effects. They are not individual excitatory anatomical
  synapses. Transferring signed weights literally to excitatory fly synapses
  would change the interpretation of the model.

## Consequences for the proposed upgrade

This is a useful reference implementation and test harness. It is not yet the
validated online update for Daniel's circuit. Two fixed-delay amplitudes do not
uniquely determine the four kernel parameters of appendix Eqs. 3.2–3.3; the
published fitting procedure did not identify a general timing-response curve.
The model is aversive PPL1 conditioning, whereas our existing pilot uses
appetitive PAM stimulation. Physiological baselines, compartment mappings,
receptor/timing dynamics and reward pathways require separate evidence.

The immediate unresolved item is the exact code/constants/parameter sample set
used to export the published Figure 5c source workbook. A concise unsent author
query is saved in `author_query_draft.md`. Nothing was sent to anybody.
Once that discrepancy is resolved, preserve the result as a reference regression
test, then validate a separately specified online mechanism before adapting the
spiking circuit. The original reference gate must not be replaced by an easier
navigation or curve-shape test.

## Reproduce

From the repository root, after the existing `.venv` is installed:

```powershell
.venv/Scripts/python.exe scripts/check_huang2024.py
```

The command intentionally returns exit code 1 while the figure gate fails.
`results/huang2024/checks.json` distinguishes software success from the failed
figure reproduction. The tests alone can be run with:

```powershell
.venv/Scripts/python.exe -m unittest discover -s tests -v
```

Sources are pinned in `provenance.json`; publisher MD5 and local SHA256 hashes
are retained. Original author files and publisher workbooks are unmodified.

## Sources

- [Paper](https://pmc.ncbi.nlm.nih.gov/articles/PMC11525173/)
- [Author repository at audited commit](https://github.com/schnitzer-lab/Luo_Huang_2024_MB_model/tree/5d7c08a9a88f923169a0c3008aca68af421e9a7f)
- [Supplementary equations and parameters](https://static-content.springer.com/esm/art%3A10.1038%2Fs41586-024-07819-w/MediaObjects/41586_2024_7819_MOESM3_ESM.pdf)
- [Figure 5 source data](https://static-content.springer.com/esm/art%3A10.1038%2Fs41586-024-07819-w/MediaObjects/41586_2024_7819_MOESM10_ESM.xlsx)
