# Motor identity resolved by image correspondence; preliminary response fit

2026-09-09. The previous investigation was too restrictive about requiring a
textual crosswalk. Comparing the actual reconstruction with the published atlas
provides evidence for the missing link. No neural simulation was run.

## Identity evidence

Public cell 160 resolves to root `648518346496932836` through the
[public mesh manifest](https://storage.googleapis.com/lee-lab_female-adult-nerve-cord/meshes/FANC/FANC_neurons/meshes/160:0).
Its actual XY mesh projection matches MN 44 in
[atlas Figure A12, PDF page 32](https://faculty.washington.edu/tuthill/docs/azevedo24_appendix.pdf).
The atlas assigns that neuron to GMR22A08-Gal4, the intermediate tibia-flexor
class studied by [Azevedo et al. 2020](https://elifesciences.org/articles/56754).

`scripts/match_motor_atlas.py` compares all five main-flexor panels. It fits
alignment on the anterior portion and scores withheld posterior branches.
Central held-out mean truncated distances are 4.046, 3.481, 4.499, **2.036**,
and 4.066 pixels for MN 41 through 45 respectively. MN 44 wins with all three
foreground threshold perturbations. The soma and side branch also match visually.

This is same-reconstruction image correspondence, not a new genetic experiment,
an independent animal validation or a probability estimate. It inherits the
authors' EM-to-driver assignment. Crops, projection and thresholds are explicit
analysis choices. Rank 3 alone remains insufficient evidence.

## Implemented response approximation

`flyplasticity/figure_twitch.py` fits a causal three-parameter gamma pulse to
probe displacement digitized from published Figure 4B's intermediate one-spike
example. Peak displacement is **4.423 micrometres**, time to peak **21.437 ms**,
and in-sample RMSE **0.214 micrometres**. Threshold and baseline sensitivity
variants are retained in `results/published_twitch/report.json`.

This fits the visible bundle of figure strokes, not individual trials. It is
a descriptive approximation, not raw-recording calibration or validation of
neuron dynamics. Delay includes sampling and probe effects. Probe displacement
is not unloaded joint angle or muscle force. No somatic spike threshold is
inferred. Runtime neural attachment remains disabled.

## Remaining raw-data work

Dryad API downloads require authentication, but the ordinary public browser
download links work without an account. Selecting Chrome by its returned ID
resolved the browser alias attachment failure. Downloads of `180222_F1_C1.zip`
and `180405_F3_C1.zip` started, but only partial files were obtained at this
checkpoint. No complete archive was verified or analyzed.

Author code is pinned to FlyAnalysis commit
`c68159f1f7a4ecc957c708ae8411fd2550482f63`. Dataset3 identifies intermediate
CurrentStep2T trials 98:126 for 180222 and EpiFlash2T trials 42:125 for 180405.
The author's single-spike analysis explicitly excludes 180222's whole-cell
spiking assay; do not pool it as equivalent optogenetic force validation.

Next: verify archives against Dryad metadata hashes, inspect per-trial MATLAB
data, resolve probe pixel-to-micrometre calibration and actual frame times,
honor exclusions, and fit single-spike responses with held-out trials. A second
animal is required for cross-animal validation. Keep passive somatic resistance,
spike recruitment and loaded probe dynamics as separate fits.

## Reproduction and checks

Downloaded inputs stay ignored under `data/`. Exact input hashes and URLs are
in the two result JSON files. Download the mesh URL from the match report to
`data/motor_physiology/cell160_mesh.bin`, and the atlas PDF to
`data/motor_targets/azevedo24_appendix.pdf`. Render using:

```powershell
pdftoppm -f 32 -singlefile -scale-to 2000 -png data/motor_targets/azevedo24_appendix.pdf data/motor_physiology/atlas_A12
.venv/Scripts/python.exe scripts/match_motor_atlas.py --out results/motor_atlas_match_repeat
```

Download the figure URL recorded in the twitch report to
`data/motor_physiology/figure4.jpg`, then run:

```powershell
.venv/Scripts/python.exe scripts/fit_published_twitch.py --out results/published_twitch_repeat
.venv/Scripts/python.exe -m unittest discover -s tests -v
```

88 offline tests pass, including malformed mesh rejection, out-of-frame scoring,
causal pulse behavior and recovery of known parameters. These software tests
are separate from the empirical evidence and do not establish biological accuracy.
Zero neural steps and no new sensory exposures; this is not a welfare assessment.
