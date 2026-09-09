# Motor physiological identity: candidate narrowed, calibration incomplete

2026-09-09. **The selected cell is not yet physiologically identified with enough
confidence to assign a fitted response.** This checkpoint records the exact gap
and measured class targets, rather than converting a candidate into a fact.

## Identity chain

| Link | Evidence/status |
|---|---|
| FANC root `648518346496932836` → main tibia flexor, source rank `3` | Previous pinned author connectivity table |
| Same root → public cell ID `160`, soma supervoxel `72764237826748104` | Exact lookup in public CAVE v1444 `cell_ids_v2` |
| Public cell 160 → left T1 leg motor neuron, L1 bundle | Published-neuron viewer tags |
| Atlas MN #44 → GMR22A08-Gal4 | Figure A12, visually inspected |
| R22A08 → intermediate flexor physiology | Azevedo 2020 |
| Root/cell 160 → atlas #44 | **Unconfirmed candidate link** |

The [author's named fast-neuron scene](https://github.com/EllenLesser/Azevedo_Lesser_Phelps_Mark_2023/blob/ff363505fd1236e63ee77966239e99280fe1ba12/jsons/fast_tibia_flexor.json)
instead selects root `648518346484809885`. Both roots occur separately in the
same published main-flexor scene. Therefore copying the named fast unit's
calibration onto our selected root would be unsupported.

The [atlas supplement, Figure A12](https://media.springernature.com/original/springer-static/esm/art%3A10.1038%2Fs41586-024-07389-x/MediaObjects/41586_2024_7389_MOESM1_ESM.pdf)
identifies #44 with the 22A08 recording line and #45 as the fast flexor. Rank 3
is suggestive of #44, but the author's parser extracts rank from a cell-type
suffix, not a physiological measurement. Two other main-flexor cells have rank
0, so arithmetic conversion from rank to atlas number is not an exact crosswalk.
The public annotation tags retrieved here do not include an atlas number or
genetic driver. No morphology registration/NBLAST match was run in this step.

## Conditional response targets and implemented unit calibration

[Azevedo et al. 2020](https://elifesciences.org/articles/56754) reports rounded
intermediate-class values of -60 mV resting somatic voltage, 300 Mohm input
resistance and zero resting firing. A local Ohmic calculation predicts -61.5 mV
under the -5 pA hyperpolarizing assay. This does **not** supply a spike threshold:
the authors discuss electrical separation of soma and spike-initiation region.

Their example intermediate single spike produces roughly 1 uN, while force
varies across recorded cells and spike counts. The experimental probe has
stiffness 0.2234 N/m, effective mass 0.17 mg and drag 0.14e-3 kg/s. Its inferred
force includes displacement, velocity and acceleration. Five micrometres of
static deflection gives 1.117 uN; treating that displacement as joint angle,
muscle force, or joint torque would be incorrect.

`flyplasticity/motor_calibration.py` implements the restricted hyperpolarizing
reference prediction and dimensionally correct probe force conversion. It rejects
depolarizing extrapolation and unconfirmed cell identity. These are offline
analysis utilities with published reference constants, **not a new fitted neural
or muscle model**. Neither probe mass nor its damping is assigned to the fly leg.

## Raw recordings located, access not obtained

The earlier investigation missed the article's final data-availability statement.
The [physiology data are publicly listed on Dryad](https://datadryad.org/dataset/doi:10.5061/dryad.76hdr7stb),
version 105831, approximately 48.76 GB total; downloading everything is unnecessary.
The [author's analysis scripts](https://github.com/tony-azevedo/FlyAnalysis/tree/c68159f1f7a4ecc957c708ae8411fd2550482f63/Records/Azevedo_2020_Records)
identify intermediate recordings including `180222_F1_C1` and `180405_F3_C1`.
The [archived README](https://zenodo.org/api/records/4527659/files/README.txt/content)
describes per-trial MATLAB files with measured voltage, stimulus parameters,
spike detections and probe tracking.

Here, the file-stream endpoint returned HTTP 403, and API download returned HTTP
401 requiring a bearer token. Browser attempts failed to attach/time out. Public
metadata and the archived analysis scripts were accessible. **No recording archive
was downloaded, no response fit was performed, and no held-out fit was validated.**

To finish: obtain the exact cell-to-driver/atlas crosswalk, then accessible raw
recordings for that unit type. Fit passive voltage response, recruitment and
spike-conditioned probe-force dynamics separately; preserve cell/trial provenance,
hold out entire recordings and retain uncertainty between flies. Only after
mechanical conversion and telemetry review can these inform an embodied run.

## Verification and recovery

Run `.venv/Scripts/python.exe scripts/audit_motor_physiology.py --out results/motor_physiology_repeat`
with a fresh output directory. Missing sources are retrieved against the checked-in
SHA256 manifest; changed sources are rejected. Outputs preserve the candidate
status and unknown threshold. The full suite passes **85 tests**, including unit
conversion, force sign/dynamic terms, malformed arrays and refusal to promote rank
to physiological identity.

All work was source inspection, static joins and algebraic/offline software tests.
**Zero neural steps**, no new sensory exposure, no aversive training. This is not
a test for absence of suffering; live neural attachment remains disabled.
