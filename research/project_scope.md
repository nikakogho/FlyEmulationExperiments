# Project scope and connectome decision

2026-09-09. Recommended working scope; migration has not been implemented.

## Objective

Build a visible, physically embodied fly model that acquires a cue preference
through local neural plasticity. Compare learning mechanisms for both behavioral
effectiveness and agreement with independent biological measurements. Report
those two outcomes separately: higher task performance does not establish higher
biological accuracy.

The first target is one appetitive association in a simple 3D arena, followed by
a reward-free choice test with swapped cue locations. This is a scoped circuit
model, not a claim to have recovered an individual fly's mind or memories.

## Dataset decision

Prefer **MaleCNS v1.0 as the candidate anatomical backbone for the next motor
integration**, subject to a targeted circuit audit. Preserve the existing FAFB
experiments as a reproducible baseline. Do not transplant their learned weights
or neuron identifiers into another animal.

Google's September 3 announcement describes a joint project with brain and VNC,
over 166,000 neurons and 125 million synaptic connections. The portal dates v1.0
to June 8, 2026; the recent announcement accompanies publication, not the first
availability of VNC data. Sources: [Google](https://www.research.google/blog/a-connectomics-milestone-mapping-the-complete-male-fruit-fly-brain/),
[project and release history](https://male-cns.janelia.org/),
[downloads](https://male-cns.janelia.org/download/).

Female BANC also joins brain and cord. Its paper supplies body-target annotations
and reports lower synaptic assignment completeness than MaleCNS under its stated
definitions. Both omit the lamina and ocellar ganglion; FAFB includes these
regions. Thus neither is a complete replacement for all early vision anatomy.
Use BANC as a comparison and annotation resource; choose it for a particular
circuit if its recovered cells and targets are better supported.
[BANC paper, anatomy and methods](https://www.nature.com/articles/s41586-026-10735-w).

Any cross-specimen reconstruction must record source, version, cell-type match,
laterality and confidence for each interface. A matched cell type is not the
same physical neuron. Missing branches and unassigned connections are unknown,
not proven absent. Synapse counts do not directly determine physiological
weights, receptor signs, time constants or plasticity rules.

## Current evidence and limits

The existing model has real 3D body physics and explicit spectral input. Its
visual adapter pools spatial information and drives selected mushroom-body cells
through an engineered mapping. Its walking controller is engineered; it does not
map individual motor neurons to muscles. Stationary probes show learned response
changes, but the latest 18 physical choice episodes did not demonstrate learned
approach. None of the three seeds beat both controls on the declared criterion.
See [preserved spectral results](spectral_vision.md).

Increasing neuron count cannot by itself fix these interfaces. Conversely, the
negative behavioral result does not establish that local plasticity is hopeless.

## Implementation sequence and concrete deliverables

1. **Audit one motor circuit in MaleCNS.** Export a versioned, small candidate
   foreleg circuit with sensory afferents, interneurons, motor cells and muscle
   target evidence. Record omitted inputs and uncertain matches. Compare relevant
   annotations against BANC/FANC/MANC. Deliver a machine-readable mapping and a
   clear implementable/not-yet-supported assessment; do not download EM imagery.
2. **Show one physical sensory-motor loop.** Connect a supported motor unit or
   antagonist pair to a simulated joint and return joint state through an
   explicit proprioceptive model. Show the live 3D joint, neural activity, muscle
   activation and feedback together. Test direction, range, force and stability;
   then test neural and feedback ablations. A driven joint proves coupling, not
   autonomous walking. Expand locomotion only as the circuit evidence permits.
3. **Repair the visual route.** Preserve spatial receptor samples and spectral
   channels. Select a documented early-vision pathway and validate response sign,
   timing and selectivity against independent measurements. Model missing anatomy
   explicitly using a declared source or approximation. No cue identity, target
   coordinates or desired steering command may enter the neural input adapter.
4. **Demonstrate closed-loop sensory control with plasticity off.** Use a simple
   visual orientation assay appropriate to the validated pathway. Deliver an
   interactive 3D scene, traces and sensory/circuit ablations. A reflex or innate
   preference is labeled as such; it is not scored as acquired memory.
5. **Run one controlled learning experiment.** Compare the current learning rule
   against a compartment-specific, modulatory local rule with an eligibility
   trace. Fit biological parameters on independent neural data, freeze those
   choices before behavioral evaluation, and compare matched training budgets.
   Use appetitive cue pairing, unpaired/yoked reward and frozen-plasticity
   controls. Test without reward or ongoing weight updates; counterbalance cue
   identity and location and use held-out layouts and independent seeds.

Learning outcomes: acquisition rate, cue specificity, retention and behavioral
preference, with uncertainty across independent seeds. Accuracy outcomes:
agreement with held-out physiology and the effects of documented interventions.
Choose confirmatory sample size from a pilot variance estimate before inspecting
confirmatory outcomes. Preserve failures and exploratory analyses separately.

## Boundaries that keep this achievable

- One fly, walking/joint mechanics, one sensory task, one learning comparison.
  Full free flight, comprehensive social behavior and new game adapters are
  later extensions, not prerequisites.
- A live viewer is an early deliverable. It must label engineered control versus
  neuron-driven control and measured versus assumed mappings.
- Calibration of mechanics and neural dynamics is legitimate. A controller that
  already knows the destination cannot count as evidence that the circuit learned
  navigation. Decoder-only and randomized-connectivity controls address different
  causal claims; include them where those claims are made.
- Benchmark the small circuit on CPU and the available RTX 5060 before scaling.
  Report memory and simulated-seconds per wall-second. Do not assume the GPU
  accelerates the physics engine or that a full CNS will run in real time.
- Keep sensory background and feedback coherent, without aversive conditioning,
  starvation, threats or injury. These choices reduce intended adverse exposure;
  they do not establish absence of subjective experience. Reward variables are
  not measurements of pleasure.
- If sensory-motor validation fails, resolve or narrow that component before
  interpreting a learning failure. If a validated task shows no improvement over
  controls, retain the negative result rather than relabeling movement as learning.

## What the viral demos tell us

The Oruk emotion demo uses 499 fixed recurrent cells and trains an external
readout. Its reported fly-versus-scrambled scores are 16.84% versus 16.88% mAP,
so it reports no wiring advantage. This is relevant reservoir-computing work,
not evidence of online plasticity inside a fly circuit. This review inspected
the author's methods/results page, not an independent reproduction.
[Author's report](https://oruk.ai/research/we-taught-a-fruit-fly-to-read-human-emotion).

An indexed announcement attributes Fly Escape Room to David (@dzhng) and claims
166k-neuron NPCs. Its implementation was not located in this bounded search; no
conclusion about its neural control or learning is justified from that claim.
[Indexed announcement](https://kyawgyii.twstalker.com/yoheinakajima).

For any demo, inspect the actual input representation, simulated circuit,
trainable components, output controller, unseen-task evaluation and controls.
A game can be a useful visualization or benchmark without demonstrating a
biological learning mechanism. Adopt useful code after auditing those boundaries;
do not make matching the headline the project's success criterion.
