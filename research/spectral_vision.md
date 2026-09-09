# Spectral vision revision

The active experimental sensory path now uses explicit wavelength spectra,
not RGB features or grayscale. Earlier scripts and results remain reproducible
as legacy experiments; they were not silently relabeled as spectral simulations.

## Biological basis and measured scope

Drosophila has broad Rh1 outer receptors, UV-sensitive Rh3/Rh4 R7 subtypes,
and blue/green-sensitive Rh5/Rh6 R8 subtypes. Pale ommatidia pair Rh3 with Rh5;
yellow ommatidia pair Rh4 with Rh6. This is not three independent idealized
UV/blue/green filters at every location.
[Sharkey et al. 2020](https://www.nature.com/articles/s41598-020-74742-1).

The source workbook in the authors' supplementary archive contains means and
standard deviations of red-eye single-opsin-rescue responses. Extraction uses
Sheet 1, D3:N50, covering the common measured range 315-550 nm at 5 nm spacing.
Each mean is normalized within that band. We preserve raw means and SDs,
source URL, cell range and SHA256 in `data/spectral/`.

These are empirical relative ERG response filters. Integrating them against
incident photon spectra is an explicit linear approximation, not a fitted
single-photoreceptor transduction model. Cross-genotype response amplitudes
do not establish relative cellular gains. In particular, the Rh6 maximum in
our truncated band is not its full-spectrum peak. Out-of-band inputs are
rejected. No spectral tails are invented or RGB-to-UV reconstruction attempted.

## Implementation

`flyplasticity/spectral.py` integrates photon spectral radiance with five
separate response curves. A fixed seeded mosaic supplies one R7 and one R8
subtype at each ommatidium, plus a broad outer-receptor response. The assumed
30% pale fraction is a population approximation, not this specimen's measured
mosaic. Dorsal rim specialization, polarization, adaptation kinetics and photon
noise are not modeled. The broad channel represents an outer-receptor response,
not six separately reconstructed photoreceptors.

The 3D renderer uses the actual FlyGym eye cameras and MuJoCo visibility.
Each surface is assigned an explicit spectrum. Geometry IDs stay inside the
renderer, just as a conventional renderer uses material identities; neural
inputs receive only receptor responses. Surfaces have prescribed uniform
spectral radiance: shadows/interreflection and spectral material optics are
not solved. Eye geometry uses the installed FlyGym fisheye remap, generalized
to floating-point channels without its RGB/uint8 restriction. These spatial
optics remain a model assumption.

The calibration scene uses equal-total-photon emitters centered at 365, 450
and 525 nm, each with Gaussian sigma 5 nm, on a nonzero broadband background.
Human-display RGB is irrelevant to the sensor. A regression test randomly
changes display RGB and verifies identical spectral eye responses. Spectral
integration can precede spatial sampling because both operations are linear.

## Executed next steps

1. Retrieved and extracted published response data, retaining provenance.
2. Implemented and tested spectral integration and an R7/R8 mosaic.
3. Rendered all three stimuli through the actual 3D eye geometry. All were
   visible and distinguishable across 721 ommatidia per eye. No physics steps
   or neural simulation were needed for this calibration.
4. Ran a stationary neural-memory probe using those recorded inputs with
   paired, delayed-reward and frozen-plasticity controls, seeds 201-203.
5. Extended the probe to train each of UV, blue and green, to check whether
   effects follow cue identity rather than one chosen colour or response scale.

The 27 neural acquisition conditions completed (three trained wavelengths,
three seeds, three conditions), each with three reward-free cue readouts.
All passed the initial absolute-response selectivity screen. A subsequent
fractional-response analysis exposed substantial generalization: after blue
training, mean suppression was 51.3% for blue and 52.9% for green. Therefore
the initial screen alone would overstate cue specificity. Counterbalancing
which cue was trained still gave positive interactions for every cue pair
and seed (blue/green interaction 0.040-0.059). This supports a stimulus-dependent
plasticity component in the engineering model, with broad cross-cue effects.
It does not validate a biological memory rule or stronger learning than Daniel's.

The reward-free embodied transfer protocol is recorded in
`results/spectral_garden/protocol.json`. It compares the saved blue-trained
paired/delayed/frozen weights at both cue arrangements for each seed, with
unchanged motor readout and exploration. Spectral images update from the actual
moving eye cameras. The neural weights are frozen during these body tests.
This is a test of transfer of stationary conditioning to movement, not a test
of spontaneous food-contact acquisition. Its outputs are evaluated separately
from neural memory. The first two completed episodes were preserved when the
remaining independent seeds were resumed in parallel; no completed episode
was replaced or selected by score.

The neural probe uses the existing 8,991-neuron subnet. A fixed engineering
adapter pools each receptor subtype, subtracts a separately recorded neutral
background, and uses a prechosen gain of 30. Five channels drive balanced
random groups of visual KCs. No cue identity, location or reward label enters
this encoder. Nevertheless, this is still a synthetic KC interface: it bypasses
the aMe12 route and visual opponency. The existing synthetic PAM reward drive
and pooled LTD kernel remain in this diagnostic. Thus this run tests whether
spectral signals can affect memory, not improved or anatomically validated
neuroplasticity. Whole-eye pooling is appropriate only for this stationary
diagnostic and is not the intended final spatial navigation interface.

Acquisition lasts 2 simulated seconds: 0.5 s cue presentation, with simultaneous
reward in paired/frozen controls or reward after a 1 s gap in delayed controls.
Reward-free tests use restored common neural initial states and learned weights,
with learning disabled. Plastic and nonplastic weight invariants are checked.
The predeclared blue absolute-response screen is preserved in its original run.
Counterbalanced fractional-effect analysis is an explicitly subsequent audit,
not a retroactive replacement of that screen.

## Embodied result

All **18 reward-free physical episodes completed**, with no neural weight
changes during testing. **No seed passed the predeclared requirement that
paired training beat both controls** after averaging the swapped positions.

The score is distance-to-green minus distance-to-blue, averaged over time and
both cue arrangements. Positive values favor blue; all paired means were negative.

| Seed | Paired score (mm) | Delayed-reward control | Frozen control |
|---|---:|---:|---:|
| 201 | -1.374 | -0.742 | -1.057 |
| 202 | -1.075 | -0.774 | -2.278 |
| 203 | -1.492 | -1.073 | -1.356 |

None of the 18 episodes entered the blue cue's 2.5 mm xy contact radius.
These results do not demonstrate learned approach to the trained light.
They also do not show that spectral encoding failed: the sensory calibration
and stationary memory results are separate evidence. The approximate visual
projection adapter, broad learned changes and pooled motor readout remain
unresolved. No parameters were tuned against these trajectories.

Evidence: `results/spectral_garden/analysis.json`, its preserved protocol,
all 18 per-decision logs, and `results/spectral_garden/trajectories.png`.
The 51 base unit tests pass (`results/spectral_unit_tests.log`); source hashes
are in `results/spectral_summary/source_manifest.json`.

## Reproduction

The next biological component to investigate is early colour opponency, rather
than replacing spectral channels with grayscale or optimizing a steering gain
against successful trajectories. Experiments find reciprocal inhibition between
R7/R8 terminals and additional feedback inhibition.
[Schnaitmann et al. 2018](https://pubmed.ncbi.nlm.nih.gov/29328919/).
Our empirical excitation filters do not implement that circuit. Its absence
is a plausible contributor to broad representations, not an established cause
of the observed generalization. Any implementation should first reproduce
independent neural response measurements before a behavioral comparison.

```powershell
.venv/Scripts/python.exe -m unittest discover -s tests -v
.venv/Scripts/python.exe scripts/check_spectral_scene.py --out results/spectral_scene_repeat
.venv/Scripts/python.exe scripts/probe_spectral_memory.py --out results/spectral_memory_repeat
.venv/Scripts/python.exe scripts/probe_spectral_memory.py --train-nm 365 --out results/spectral_memory_uv_repeat
.venv/Scripts/python.exe scripts/probe_spectral_memory.py --train-nm 525 --out results/spectral_memory_green_repeat
.venv/Scripts/python.exe scripts/plot_spectral_results.py
.venv/Scripts/python.exe scripts/spectral_garden.py --out results/spectral_garden_repeat
```

Probe scripts read the preserved original spectral scene. Output directories
must be new. Source extraction uses `scripts/extract_spectral_data.py` with
the bundled Python/openpyxl runtime; simulations need only the extracted NPZ.
The final plotting script reads the named original cohorts, not repeat folders.
`spectral_garden.py --resume --seeds 201` can resume a subset of the original
protocol in the same output directory. It rejects incompatible saved episodes.
There are no output videos for this cohort; trajectories and sensory/motor
values are saved per decision. `results/spectral_summary/` contains inspected
scientific figures of receptor curves, 3D retinal channels and memory effects.
