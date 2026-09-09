# Games, GPU feasibility, and the next plasticity experiment

Audit date: 2026-09-08. This supplements `assessment.md`; it does not establish a whole-brain upload or superiority over real flies.

## The specific Minecraft project

The user identified [Fly Project](https://flyproject.io/). Its public page describes extracted escape, steering and compass circuits, including 429-neuron escape and 739-neuron steering demonstrations. The route demonstration explicitly begins with an implanted route memory. It also discloses roughly 150 ms sensing polls, which constrain reaction-time interpretation. The page lists a public playable build as forthcoming; I found no source-code link there. Consequently, I cannot verify its implementation or learned behavior from this page. Its claims of uploaded consciousness are not established by the supplied evidence. A connectome-derived simulation is not a recording of a living animal's ongoing neural activity.

An implanted route can test execution of stored vectors. It does not test acquisition, retention, generalization or reversal of a route. These require before/after measurements and controls.

## Other Minecraft implementations inspected

These are separate projects; do not attribute their code to Fly Project.

- [blendi-remade/fly-brain-minecraft](https://github.com/blendi-remade/fly-brain-minecraft), locally pinned at `6cfa30175003ef25da68a237d5eda958f8047b82`. Java/Fabric bridge and spike telemetry are useful examples. `FlyBody.java` lines 44–80 implements food-directed steering, collision responses and exploration when the reflex layer is enabled (the default). Its documentation explicitly distinguishes these supports from neural behavior. The inspected `LifNetwork.java` propagates fixed connectome weights and gives neuromodulators no fast synaptic effect; it supplies no dopamine-dependent synaptic learning mechanism. No game execution or behavioral replication was performed.
- [evnsnclr/neurocraft-fly-public](https://github.com/evnsnclr/neurocraft-fly-public), pinned at `d121466b3ba2f11498e6da498c74acb061bb00eb`. Public documentation, not a ready runnable release. It explicitly describes labeled neural readouts selecting scripted body programs. Useful reporting discipline, not evidence that all movement or skills emerge from the connectome.

## What a game interface can legitimately do

Minecraft is feasible as an embodiment and evaluation interface. Other games are feasible if they expose reproducible observations, actions, resets and simulation timing. A different NPC body can be a visual/motor mapping; it does not itself add neural capabilities. High-level yaw, forward movement and jump commands do not reproduce six-legged insect biomechanics.

For our experiment, define the learner's information boundary first. Supply modeled local sensory signals; decode neural output into a fixed action interface. Disable native goal selection/pathfinding. Keep global source coordinates, shortest paths, object reward labels and evaluator success flags out of the learner. A fixed gait/controller is a declared body abstraction; an external policy that chooses food or solves the route confounds a claim about neural learning. Freeze encoders and decoders across plasticity conditions.

Retain the existing MuJoCo garden for initial transfer testing. It already provides genuine 3D terrain and a known failure baseline. Adding a game port now would introduce more unvalidated sensory and motor choices.

## Biology target

[Huang, Luo et al. (Nature, 2024)](https://pmc.ncbi.nlm.nih.gov/articles/PMC11525173/) provides a concrete reference: a reduced model of the γ1, α2 and α3 mushroom-body modules, with compartment-specific dopamine, bidirectional KC→MBON plasticity and MBON→DAN feedback. It was fit to neural measurements and used to predict subsequent experiments. Its supplementary information contains equations and fitted parameters. This is aversive conditioning and a reduced rate model, so transferring it into our appetitive spiking circuit requires explicit validation. It is not a drop-in whole-brain replacement. [Deposited data](https://zenodo.org/records/10998457) include voltage-imaging and behavioral archives; their listing is not evidence of a runnable model-code release.

For temporal sign dependence, also consult [Handler et al. (Cell, 2019)](https://pubmed.ncbi.nlm.nih.gov/31230716/). For reversal through punishment omission, consult [the 2021 primary study](https://www.nature.com/articles/s41467-021-21388-w). Different compartments/protocols should not be collapsed into one universal dopamine rule.

## Proposed sequence and decision criteria

1. Reproduce a published reduced model using its equations and fixed parameters before adapting it. Record numerical tolerances and which plotted experimental measurements are matched.
2. Add compartment-specific eligibility and dopamine-dependent changes to the spiking model. Specify both strengthening and weakening, baseline dopamine, bounds and decay. Do not use an episode reward Boolean inside the synaptic update.
3. Match one conditioning protocol across Daniel's rule, our temporal-only pilot, compartment-only and combined variants. Run paired, unpaired, backward, dopamine-blocked, plasticity-disabled, extinction and reversal conditions. Evaluate retention and interference as well as training response.
4. Freeze parameter selection on training conditions. Evaluate held-out odors, delays and seeds. Check neural activity stability and preservation of previously reproduced circuit responses.
5. Only then test transfer to the 3D garden, counterbalancing source identities/locations with fixed duration and an unchanged controller. Test a game port after this boundary is working.

The current pilot only demonstrates a candidate temporal LTD mechanism. It lacks bidirectionality, compartments and biological calibration. The existing 3D test failed to reach the rewarded source in both conditions. Neither is an improvement claim.

Separate **accuracy** (agreement with fly physiology and behavior) from **enhancement** (better specified task performance). Improving a weak simulation is not automatically exceeding a real fly. Faster reversal, longer retention or greater associative capacity are reasonable measurable hypotheses; broad game competence or general intelligence is unsupported. If improvement vanishes when scripted/oracle information is removed, reject the learning claim. Failure of one reduced model is not proof that all fly emulation is hopeless.

## Daniel's repository and runtime

`upstream/fly-api` remains at `a6ad07a810b1a43cd0356149c07b32105eb46d2a` after refreshing origin. Its learning notes report that broad spike-frequency adaptation and global short-term depression damaged a feeding response while addressing runaway activity. These are upstream reports, not rerun findings. Use them to motivate local interventions and preservation tests, rather than globally turning up adaptation. The repository supplies no ready GPU backend.

The local device is an RTX 5060 Laptop GPU, approximately 8 GB VRAM. `scripts/profile_runtime.py` measured warm 150 ms neural probes at about 0.38–0.41 seconds, while one 150 ms body segment took 5.10 seconds under cProfile. This single-segment profile is not a whole-run throughput measurement. Observation generation, MuJoCo calls and controller work dominate the body path. The active OpenGL renderer reported Intel integrated graphics.

An isolated `.venv-gpu` installs CuPy with CUDA runtime components. `scripts/benchmark_gpu.py` checks a float64 weight-update kernel against NumPy on the 62,261 saved plastic weights, using synthetic eligibility and batches of parameter settings. It excludes the live spiking network, physics, rendering and biological learning quality. Results are in `results/performance/gpu_benchmark.json`; do not call its speedups whole-simulation speedups.

Optional reproduction:

```powershell
uv venv .venv-gpu --python 3.12
uv pip install --python .venv-gpu/Scripts/python.exe -r requirements-gpu-lock.txt
.venv-gpu/Scripts/python.exe scripts/benchmark_gpu.py
```

[CuPy installation documentation](https://docs.cupy.dev/en/stable/install.html) supports runtime-component installation without a system toolkit. [Brian2CUDA's installation guide](https://github.com/brian-team/brian2cuda/blob/master/docs_sphinx/introduction/install.rst) requires Linux and CUDA tooling; it is not an automatic switch for this native Windows setup. [MuJoCo Warp](https://mujoco.readthedocs.io/en/latest/mjwarp/) is a possible future batched physics port, not something enabled in our existing FlyGym runs.
