# Fly emulation experiments

Learning track: [controlled association results](research/association_results.md).
Three guarded four-second arms completed with recovery. Pairing produced a
cue-selective persistent weight change and greater output-response reduction
than unpaired/frozen controls. The predeclared pilot gate narrowly missed:
14.95098% selectivity versus 15%. No threshold was changed or extra run added.
118 tests pass. Biological accuracy, absence of suffering and learned 3D approach
are not established; the failed leg-calcium fit does not block this learning track.

Current delivery: [3D mechanical preview and calibration status](research/delivery_checkpoint.md).
Double-click `view-arena.cmd` for the recorded 3D scene. The local video is
`results/delivery_arena/fly_in_3d.mp4`. This shows scripted mechanical walking,
turning and rest, **not learned behavior**. The seven-step neural-learning delivery
is incomplete; independent learning validation and guarded embodiment remain.

Checkpoint policy: significant tested milestones are committed and pushed.
Git retains code, tests, dependency locks, research notes and text result evidence.
Downloaded datasets, local environments/upstream checkouts, generated media and
binary arrays remain local and must be downloaded or regenerated after cloning;
this repository is not a backup of those artifacts. See `.gitignore` and the
setup scripts for exclusions and pinned input sources.

Latest: [raw motor-response calibration](research/raw_motor_calibration.md).
Both recording archives are verified, raw single-spike probe fits outperform the
earlier figure approximation on evaluation trials, and 95 offline tests pass.
The second recording has a documented genotype-label conflict. These are passive
somatic/probe-response fits; full motor dynamics and M3 remain incomplete.
No neural or embodied execution was enabled.
Previous: [motor identity match and preliminary response fit](research/motor_identity_resolution.md).
Previous: [minimal-reflex assay and calibration finding](research/minimal_reflex_progress.md).
Previous: [exact FANC sensory-to-muscle pathway and anatomical foreleg test](research/fanc_pathway_and_foreleg.md).

**Current direction:** [project scope and MaleCNS migration assessment](research/project_scope.md).
See [testable milestones and the welfare execution constraint](research/milestones.md).
The target is a visible 3D sensory-motor model with controlled tests of local
plasticity. MaleCNS integration is proposed, not implemented; the latest spectral
experiment did not demonstrate learned approach.

Local reproduction and audit of Daniel Tan's 2026-09-08 conditioning/navigation
demo, plus an exploratory temporal-plasticity modification.

**Read [the investigation](research/assessment.md).** This is a connectome-derived
olfactory/mushroom-body subcircuit with an engineered body controller, not a
validated whole-organism upload. The temporal pilot is not a validated biological
upgrade or a demonstrated navigation improvement.

## Run on Windows

This workspace already has the data, upstream repositories, and a working Python
3.12 environment. From this directory in PowerShell:

```powershell
.venv/Scripts/python.exe scripts/run_baseline.py learning --out results/my_learning
.venv/Scripts/python.exe scripts/run_baseline.py navigation --out results/my_navigation --n-decisions 40
.venv/Scripts/python.exe scripts/temporal_pilot.py --out results/my_temporal_pilot
```

Navigation produces `naive.mp4`, `trained.mp4`, trajectory arrays, and logs.
The temporal pilot produces summaries and final synaptic weight arrays; it does
not run the body controller. Reusing an output path overwrites that run's files.

For a fresh checkout with `uv` and Git installed:

```powershell
powershell -ExecutionPolicy Bypass -File setup.ps1
```

Upstream sources and data are pinned in `research/provenance.json` and fetched by
`setup.ps1`. They are excluded from this repository, along with the virtualenv.
`requirements-lock.txt` records the tested environment. No paid services needed.

## What was changed

### Alternate 3D environment

```powershell
.venv/Scripts/python.exe scripts/garden3d.py --out results/garden3d --steps 24
```

This runs naive and conditioned brains in a terraced garden: four shallow steps,
a raised bed, collidable stones and low edging, and two odor sources at different
positions from Daniel's arena. An oblique camera shows the physical geometry.
The body walks in 3D; this is not free flight. Odor concentrations vary in XYZ
using analytic Gaussian fields; airflow and obstacle-induced odor occlusion are
not modeled. Antenna sampling positions are approximated from body pose. Odor
dispensers are visual markers and have no collision geometry.

Both conditions receive the same 3.6 seconds of walking with identical controller
parameters and restored neural RNG state. There is no source-coordinate stopping
rule. Coordinates enter the environment's odor calculation and evaluation only.
This first environment transfer uses the original episodic learning rule, not
the exploratory temporal pilot. Videos, XYZ logs, and configuration are saved in
the chosen output directory. Success on this single layout is not evidence of
general obstacle avoidance or better neuroplasticity.

After a completed run, build a labelled comparison video and trajectory plot:

```powershell
.venv/Scripts/python.exe scripts/garden3d_results.py --out results/garden3d
```

During arena development, taller rocks caused a MuJoCo acceleration instability
at 1.1175 seconds in the naive rollout. The failed log is preserved as
`research/garden3d_initial_failure.log`; the current layout uses lower rocks.
A second run failed at the high enclosure edge at 3.1731 seconds (saved in
`research/garden3d_wall_failure.log`), so the current arena uses low edging and
visual-only odor markers. These layout adjustments are environment development,
not neural-learning results. The original tall-obstacle layouts are not validated.

The revised arena completed both 24-decision runs (3.6 seconds each), with finite
XYZ trajectories and 215 decoded video frames per condition. The conditioned
controller did not reach the rewarded source: its closest recorded body position
was 7.95 mm away, versus 7.23 mm for the naive controller. This is a transfer
failure on one layout, not evidence that conditioning improved navigation.
The low edging is traversable; both flies eventually leave the camera's central
garden view. Full trajectories are retained in JSON and plotted in
`results/garden3d/trajectories.png`.

- Upstream code remains unmodified. The baseline wrapper supplies the local
  annotation path, explicitly seeds Brian2, and uses its NumPy backend.
- Annotation data is publicly available and version-pinned; Daniel's original
  annotation file/hash was not published. Local circuit counts match his report.
- The temporal pilot changes the learning mechanism and training schedule. Do not
  interpret its three pairings versus the baseline's five as sample efficiency.
- No compartments, valence-specific output model, LTP, consolidation, or natural
  taste-to-dopamine pathway have been implemented in the pilot.

## Checks and outputs

```powershell
.venv/Scripts/python.exe scripts/check_temporal_rule.py
.venv/Scripts/python.exe scripts/record_provenance.py
.venv/Scripts/python.exe scripts/summarize.py
uv pip check --python .venv/Scripts/python.exe
```

`results/summary.json` contains measured results. `results/comparison.png` plots
the baseline and the exploratory temporal pilot. Full episodes and logs remain
available. Brian2 emits harmless local-name collision warnings; its documented
internal-variable precedence is used.

The baseline does not expose the 139k-neuron whole-brain taste demo through this
wrapper; it reproduces the learning and navigation experiments linked in the post.

## Minecraft, biological next steps, and GPU feasibility

See [the follow-up audit](research/games_gpu_plasticity.md) for the specific
Fly Project site, two separate Minecraft repositories, and a proposed
compartment-specific plasticity validation sequence. The game repositories were
inspected, not run. No new learning superiority has been demonstrated.

`scripts/profile_runtime.py` profiles the current CPU/body pipeline.
`scripts/benchmark_gpu.py` runs in the optional isolated `.venv-gpu` and tests
only synaptic weight-update arithmetic. The completed CUDA benchmark matched
NumPy within 4e-15 maximum absolute error. GPU-resident kernel speedups were
1.46x, 47.37x and 30.55x for batches of 1, 64 and 256 respectively; these are
single-run microbenchmarks, not whole-fly speedups. JSON outputs are in
`results/performance/`. Optional GPU dependencies are pinned separately in
`requirements-gpu-lock.txt`.

## Published memory-model reproduction

The [Huang–Luo reproduction report](research/huang2024/REPRODUCTION.md) records
the first validation stage. The Python port matches 144 numeric values saved
in the authors' native MATLAB figures. Fourteen software tests pass. A separate
comparison with the published Figure 5c medians fails the preset 0.05 Hz gate
(21/48 pass; maximum discrepancy 0.44 Hz). No parameters were refitted.
Spiking integration and embodied transfer of this rule remain gated.

```powershell
./setup-huang2024.ps1
.venv/Scripts/python.exe scripts/check_huang2024.py
```

The combined check intentionally exits 1 for the unresolved figure mismatch.
Read `results/huang2024/checks.json` to distinguish software test success from
the figure gate. The source port is GPL-3.0-or-later, attributed in the module
and `flyplasticity/COPYING`. The existing baseline and temporal pilot remain
separate experiments.

## Online light learning in a physical 3D scene

See [the light pilot report](research/light_pilot.md) and its
[fixed protocol](research/light_protocol.md). This experiment uses rendered eye
pixels, a local food-contact proxy, and online spike-dependent weight updates.
It contains no goal-vector controller or distance-shaped reward. The visual,
reward and motor interfaces are explicit approximations, not recovered complete
fly pathways. The final arena has a flat floor after terraced variants failed
physically. It tests ground walking and light-cue association.

Run the checks:

```powershell
.venv/Scripts/python.exe -m unittest discover -s tests
.venv/Scripts/python.exe scripts/check_light_brain.py
.venv/Scripts/python.exe scripts/diagnose_light_memory.py
.venv/Scripts/python.exe scripts/light_garden.py --preflight --out results/light_flat_preflight
```

Run a fresh single-seed experiment, including all three conditions:

```powershell
.venv/Scripts/python.exe scripts/light_garden.py --seed 0 --out results/my_light_run
```

Use a new output directory to preserve earlier results. The full recorded cohort
uses seeds 0, 1, 2 and 45 episodes. Its launcher runs independent controls
concurrently, requires successful body checks, and refuses to overwrite an
existing cohort:

```powershell
.venv/Scripts/python.exe scripts/run_light_pilot.py
.venv/Scripts/python.exe scripts/analyze_light_garden.py
.venv/Scripts/python.exe scripts/light_results_media.py
```

JSON records include eye features, spikes, motor actions, position and actual
reinforcement samples. Food-free tests explicitly restore initial neural state
while retaining learned weights. The analysis checks frozen weights and exact
shifted-reward tapes. The isolated diagnostic demonstrates retained cue-specific
response changes, but these must not be mistaken for learned approach behavior.

Completed pilot: all 45 episodes and analysis invariants pass. No learned
approach advantage was demonstrated: plastic-minus-shifted-control preference
is zero in every seed. Only one of three plastic seeds sampled food, for one
100 ms reward-input interval. The sole preference shift versus frozen weights
occurred in an unexposed seed and was matched by its no-food control. See the
report for the neural memory effect, decoder limitations and preserved physics
failures; this is not a validated improvement over Daniel's behavior.

## Sensory transport and mechanical rest checks

The [first sensory bridge validation](research/sensory_bridge_stage1.md)
preserves spatial eye images and body feedback without wiring them to the
brain. All 33 unit tests pass. Recorded-image transport checks pass; a short
body-only rest/walk/rest probe completes but fails its preset rest-speed gate.
No connectome brain or learning runs in these checks. The report includes
commands, raw evidence, limitations and the next validation gate.

Follow-up: [explicit standing](research/explicit_standing.md) passes the same
rest gate across three seeds while preserving commanded walking. All 36 unit
tests pass. This is a mechanical controller improvement; autonomous rest,
biological sensory integration and better learning remain unvalidated.

The [offline FlyVis calibration](research/vision_calibration.md) now runs the
authors' fixed visual checkpoint: 8/8 direction checks and 7/8 polarity checks
pass at both 200 and 400 Hz. Numerical tolerance checks pass; the T4d polarity
failure keeps the overall gate failed. This isolated visual model is not yet
connected to the body or learning circuit. Setup, evidence and exact limits
are in the report.

[Author-analysis comparison](research/author_polarity_comparison.md): the T4d
mismatch persists with the authors' flash metric in default checkpoint 000,
but 9/10 of their listed model set have the expected sign, and all eight
ensemble median signs agree. This identifies checkpoint variability rather
than invalidating the visual-model approach.

The [integration and learning execution report](research/integration_and_learning_plan.md)
records the next six-step plan and results: 42 unit tests pass, retinal mapping
matches FlyGym, ten visual models replay recorded 3D eye data, and a synthetic
matched-drive test isolates compartment-local plasticity. The anatomical audit
exports 62 candidate intermediate neurons. Integrated learning remains gated
on missing functional and compartment mappings; no new embodied learning
success is claimed.

[Step 4 validation](research/step4_validation.md) identifies an aMe12/visual-KC/
MBON01 candidate route and supports a coarse gamma5 compartment assignment.
An exact color-aliasing test exposed the grayscale interface's inability to
distinguish the task cues; a separate RGB-preserving interface fixes transport,
but does not supply spectral physiology. All 43 unit tests pass. The sensory
and fine modulatory mappings remain unvalidated, so conditional step 5 was
not run.

The newer [spectral vision revision](research/spectral_vision.md) replaces
RGB/grayscale in the new experimental path with explicit UV/visible photon
spectra and published Rh1/Rh3/Rh4/Rh5/Rh6 response curves. Its actual 3D eye
calibration passes and 51 unit tests pass. Three-cue, three-seed neural probes
show stimulus-dependent plasticity with substantial generalization. The
sensory-to-KC adapter is still explicitly synthetic; this is not yet a recovered
visual learning pathway. Legacy RGB scripts remain for reproducing old runs.
All 18 subsequent reward-free 3D transfer episodes completed. Paired training
did not beat both controls in any of the three seeds, and no episode entered
the trained blue cue's contact radius. Improved light approach remains unproven.
