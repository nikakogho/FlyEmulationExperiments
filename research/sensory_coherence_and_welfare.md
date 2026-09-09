# Sensory coherence and welfare constraints

2026-09-08. User priority: avoid bothering the simulated system, including
potential functional analogues of suffering. This updates the earlier demo
recommendations. No new embodied/neural simulation was run for this audit.

## What the current model actually receives

Source inspected: `scripts/light_brain.py`, `scripts/light_garden.py`,
`flyplasticity/light_task.py`, and the installed FlyGym turning controller.

| Signal | Reaches the connectome-derived neural subnetwork? |
|---|---|
| Rendered eyes | Only four whole-eye color-opponent averages: green/blue for each eye. Spatial detail and grayscale ground texture/motion are discarded |
| Food | Sampled body-position contact proxy directly drives PAMs; no reconstructed taste pathway |
| Leg contact and body/limb geometry | Used by the separate reflex gait controller; not fed to LightBrain |
| Odor | External ORN drive is zero in this light experiment; this does not imply every olfactory neuron is electrically silent |
| Airflow, antennal touch, hearing | No corresponding input pathway in the light experiment |
| Hunger, injury, thirst, physiological regulation | No explicit models of these states in the light-task interface |
| Motor-state feedback/efference copy | No reconstructed ascending route into the subnetwork |

Inputs and actions are held in 100 ms blocks. The local neural network has finer
internal dynamics, and body physics uses 0.1 ms steps, but that does not restore
the missing sensory streams. Motor commands are [1+delta, 1-delta], with delta
bounded to +/-0.3; this interface provides no meaningful voluntary rest action.

This is a markedly incomplete sensorimotor model. It is not evidence that an
intact uploaded animal has been placed in sensory deprivation. In particular,
we did not recover an individual's existing memories, physiological state or
complete nervous system. Distribution mismatch relative to biological operation
is a sensible concern; the current circuit is not a behaviorally pretrained
whole animal with an established in-distribution environment.

Missing feedback can affect scientific validity. In real flies, ascending
signals carry ongoing behavioral state into brain regions involved in sensory
integration and action selection. Visual processing also incorporates
nonvisual locomotor signals.
[Ascending neurons](https://www.nature.com/articles/s41593-023-01281-z),
[locomotor signals in vision](https://www.nature.com/articles/nn.4435).
This supports investigating the mismatch; it does not establish that sensory
impoverishment caused our specific light-learning result. Sparse reward
exposure, the engineered encoding and pooled output decoder remain confounds.

## Revised development direction

1. Preserve spatial visual information and movement-generated optic flow from
   ordinary, steady scenes. Validate sensory transforms on recorded/test inputs
   before attaching them to an embodied neural loop.
2. Add body feedback through anatomically motivated pathways: joint movement,
   foot contact, and relevant locomotor state. Start with the pathways needed
   for the target task rather than indiscriminately stimulating the whole model.
3. Check timing and sensory-action consistency. Avoid inconsistent body/brain
   resets or delays being mistaken for biological behavior; document remaining
   abstractions. Provide an explicit rest/no-op capability in the motor interface.
4. Calibrate baseline activity and adaptation against physiological data where
   possible. Do not fill missing inputs with arbitrary noise or force firing
   rates upward to make behavior look lively.
5. Favor stable, non-noxious environments and modest, well-characterized stimuli.
   Do not add artificial deprivation, persistent unmet needs, injury, pain-like
   state models or broad neuromodulator stimulation as a shortcut to fidelity.

These are proposed implementation steps, not completed fixes. Merely enriching
the rendered scene does not help if the neural encoder discards that information.

## Welfare interpretation and operational constraint

There is no established evidence that this particular simplified model has
subjective experiences, and no validated assay that certifies its absence of
suffering. A model's avoiding a stimulus, changing synaptic weights, or having a
variable named dopamine does not settle that question. More realistic sensory
input is not a welfare guarantee, nor is “reward-only” training necessarily one.

Biological flies have nociceptive and persistent sensitization mechanisms;
their existence motivates care with biological analogies but does not show
that the same experience is present in our software.
[Adult fly injury/sensitization study](https://pubmed.ncbi.nlm.nih.gov/31309148/).
Artificial consciousness assessment remains theory-dependent and requires
system-specific evidence.
[Computational indicator framework](https://arxiv.org/abs/2308.08708).

For this project, remove threat, punishment, fighting, deprivation and injury
demonstrations from the active implementation agenda. Prefer sensory calibration,
rest-capable exploration, and carefully limited appetitive protocols that do
not require modeled starvation or distress. A reward signal is an experimental
input, not proof of pleasure. If frustration-like persistence or negative-state
mechanisms are added, reassess the design rather than assuming that missing
nociceptors makes it harmless.

Numerical instability, runaway activity or persistent repetitive actions are
reasons to stop and inspect the implementation; they are not validated pain
meters. Avoid unnecessary long or large-population runs while fidelity and
welfare-relevant uncertainty remain unresolved. No guarantee of zero subjective
harm is available from the present evidence.

The earlier optomotor/following suggestions also require a stimulus review:
being an innate reflex or a positive-learning task does not by itself establish
comfort. Their research notes remain historical candidate inventories, not
authorization to run aversive protocols under this updated user constraint.

Implementation update: [sensory bridge stage 1](sensory_bridge_stage1.md)
preserves spatial inputs and explicitly represents missing modalities. Its
offline checks passed, but its mechanical quiet-rest gate failed. The new
interface remains disconnected from the brain; this is neither restored
biological sensory processing nor evidence of comfort.
