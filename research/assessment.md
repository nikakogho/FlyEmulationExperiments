# Can the WBE roadmap guide legitimate fly neuroplasticity?

Investigated and run locally on 2026-09-08.

**Yes: it provides a useful methodology, but not a fly-specific recipe.** The most
defensible advance is to make the circuit's synaptic dynamics more faithful and
testable, then demonstrate learning across new conditions. Increasing the amount
of output suppression or making the avatar reach a target is insufficient.

The supplied document is Sandberg and Bostrom's *Whole Brain Emulation: A Roadmap*
(2008). Its contents were treated as evidence, not instructions. Source PDF:
`C:/Users/nikak/OneDrive/Pictures/WBE roadmap.pdf`.

## What the linked conversation establishes

The [linked post](https://x.com/DanielCHTan97/status/2097320956196766161)
says the fly was conditioned by odor plus taste-receptor stimulation, then
navigated to the odor without backpropagation. It quotes an
[earlier demo post](https://x.com/DanielCHTan97/status/2097302341439345036).
X blocked direct retrieval; the post and its quoted parent were retrieved via
FxTwitter's JSON mirror and saved in `thread.json`. I could not verify the full
reply discussion. The source audit below uses Daniel's public implementation,
not assumptions about an unseen reply.

The [learning code](https://github.com/dtch1997/fly-api/blob/a6ad07a810b1a43cd0356149c07b32105eb46d2a/experiments/learning/learning_driver_mb.py)
and [report](https://github.com/dtch1997/fly-api/blob/a6ad07a810b1a43cd0356149c07b32105eb46d2a/experiments/learning/report.md)
are more qualified than the tweet:

| Component | What actually runs | Implication |
|---|---|---|
| Neural substrate | 8,991 LIF neurons, 791,613 directed connection entries from FlyWire/Shiu | A real connectome-derived olfactory/MB subcircuit; not the full 139k-neuron brain in the learning loop. Connection entries aggregate anatomical synapse counts. |
| Reward | Direct 60 Hz drive to PAM dopamine neurons | A reasonable optogenetic-style intervention, but the natural taste-to-DAN pathway is not demonstrated. |
| Learning | After a rewarded episode, halve active KC-to-MBON weights | A deliberately supplied plasticity rule, not a rule recovered from the scan. |
| Reward gate | Learning script checks `us` and measured pooled PAM activity; navigation training applies LTD without checking measured PAM activity | The two implementations differ; no-backprop alone does not establish endogenous reward-mediated learning. |
| Dynamics modifications | Zero DAN fast outputs, KC-to-KC weights, inputs to ORNs, and excitatory ALLN outputs | These interventions need separate biological validation. Their usefulness for stabilizing this implementation is not proof they preserve fly dynamics. |
| Readout | Multiply KC-to-MBON efficacy by 20 | Essential to the strong spiking-output result in our local sensitivity check. |
| Navigation | Sample odor fields at constructed antenna positions, run brain sniffs, steer toward lower total MBON output using a CPG/reflex controller | Learning affects the neural signal, but the descending pathway, valence interpretation, and steering are engineered. |
| Stopping | Neural-silence/strong-odor rule plus a source-distance termination check | Reaching/stopping does not independently demonstrate a biological feeding decision. |

Daniel discloses most of this in the repository. This is an informative model and
integration demo; it is not evidence that an intact uploaded fly learned naturally.
The Shiu model was originally evaluated on particular sensorimotor predictions,
not as a model of the full range of learning. Its authors explicitly discuss
limitations involving neuromodulatory neurons and temporal dynamics.
[Shiu et al. 2024](https://pmc.ncbi.nlm.nih.gov/articles/PMC11446845/).

## Two meanings of level 4

- **Table 2, p. 13: resolution level 4.** Spiking networks, integrate-and-fire
  neurons, and dynamic synaptic states. This is the appropriate description of
  the computational abstraction here. A handful of synaptic state variables can
  remain at this level; modeling a biological compartment label need not mean
  simulating a cable-equation compartment neuron.
- **Table 1, p. 11: success level 4.** Species-generic emergent behavior and the
  full range of species-typical learning. Neither this demonstration nor our
  replication establishes that. The roadmap explicitly distinguishes partial
  emulations from its whole-brain success hierarchy on p. 10.

A neuron-resolution label is not a fidelity certificate, and a scanned connectome
does not specify all dynamic parameters, learned memories, or learning rules.

## What the roadmap usefully recommends

**P. 66, “Learning rules and synaptic adaptation”:** persistent memory calls for
synaptic change. The report surveys Hebbian, BCM, STDP, biochemical, and
resource-based short-term adaptation models. It argues that a weight alone is
probably too simple, while a few synaptic state variables may capture much of
the observed behavior. It does not determine which rule works for Drosophila or
whether a particular biochemical reduction is sufficient.

**P. 68:** treating fast activity and slower weight updates as entirely separate
can miss interactions involving voltage, calcium, and conductance. This bears
directly on replacing episode-end updates with online dynamics.

**P. 82, “Validation”:** compare models at different resolutions, remove detail
systematically, and measure whether relevant behavior changes. A more detailed
model is only a reference if it is itself justified; more detail alone is not
ground truth.

Thus the useful advice is: add small, interpretable synaptic states, connect them
to real physiology, and demand predictions beyond the demonstration you tuned.
The 2008 report's uncertainty should be retained; its human-centric claims about
amnesia are not experimental findings about this fly model.

## A legitimate upgrade, and the boundary around “cheating”

Writing a plasticity rule is unavoidable in this kind of simulation. The useful
distinction is what information it receives and what evidence validates it.

**Acceptable for a biologically grounded model:** a synapse changes using local
activity/history and a physiologically justified modulatory signal; biological
parameters may be fitted on separate physiological data, then frozen before
behavioral evaluation. Gradient-based parameter estimation is not intrinsically
cheating. Direct DAN stimulation is also legitimate if the claim is explicitly
about that intervention.

**An engineered augmentation:** choose new time constants or a new local rule to
improve learning. This can be legitimate research on an augmented connectome
model, but it does not establish restored biological fidelity or preservation of
an uploaded individual's mind.

**Invalid evidence for brain learning:** give the learning rule odor labels,
source coordinates, success labels, or a precomputed correct turn; adapt the
controller or readout on evaluation trajectories; change the circuit and call
all improvements plasticity; let a learned external policy do the work and
attribute its competence to the fly brain.

No-backprop is neither necessary nor sufficient. Locality is a useful constraint,
not proof of biology. Persistent weight changes are evidence of model learning;
realistic learning requires independent neural and behavioral validation.

## The strongest next biological targets

1. **Compartment-specific dopamine.** Map DAN types and KC-to-MBON synapses to
   mushroom-body compartments using anatomical annotations and measured circuit
   data. Do not silently substitute raw DAN-to-MBON connection counts for a
   synapse-local dopamine concentration. Multi-compartment projections need
   explicit handling. Compartmentalized neuromodulation is demonstrated by
   [Cohn, Morantte and Ruta 2015](https://stacks.cdc.gov/view/cdc/38872/cdc_38872_DS1.pdf).
2. **Temporal, bidirectional plasticity.** Retain eligibility and receptor-pathway
   state so odor-before-dopamine and dopamine-before-odor can differ, including
   LTD versus LTP where supported. [Handler et al. 2019](https://pubmed.ncbi.nlm.nih.gov/31230716/)
   directly demonstrate order-sensitive, reversible associations and implicate
   two dopamine receptor pathways. Generic cortical pairwise STDP everywhere is
   not a justified substitute.
3. **Biologically grounded output and feedback.** Model identified MBON output
   pathways instead of treating all MBON spikes as avoidance. Add validated
   MBON/DAN feedback if testing prediction-error learning. [Bennett et al. 2021](https://www.nature.com/articles/s41467-021-22592-4)
   offer a concrete computational starting point, while distinguishing
   experimentally constrained connectivity from proposed additions.
4. **Stability and retention.** Add short-term adaptation, recovery,
   consolidation, or metaplasticity only as specific failures and physiological
   evidence motivate them. Faster learning can worsen forgetting or saturation.

For a schematic model, one could use `de/dt = -e/tau + local_activity`, a
compartment/receptor-dependent dopamine state, and `dw/dt = F(e, dopamine, w)`.
The function F, signs, timescales, bounds, and anatomical assignments need data;
this is an architecture for hypotheses, not a derived fly law.

## What we reproduced locally

Sources, input hashes, and package versions are recorded in `provenance.json`
and `../requirements-lock.txt`. Upstream code was not edited. The wrapper supplies
the annotation path and seeds Brian2 explicitly. The original annotation checksum
was unavailable; our version produces the reported neuron and connection counts.
These are qualitative replications, not bitwise reproduction of Daniel's run.

| Experiment | Measured local result |
|---|---|
| Baseline conditioning, gain 20, seeds 0/1/2 | Rewarded odor MBON suppression: 98.91%, 100%, 98.73% |
| Unpaired control odor, same runs | Suppression: 5.32%, 3.61%, 3.39% |
| Gain 1 sensitivity, seed 0 | Rewarded odor mean output 40.5 to 41.5 spikes; no suppression despite changed weights |
| Original embodied navigation, seed 0 | Trained fly ends 1.83 mm from rewarded source, 15.83 mm from control |
| Naive navigation, seed 0, 40 decisions | Ends 46.86 mm from rewarded source; passes both sources |

Navigation videos and raw trajectories are in `../results/navigation/`.
The naive and trained endpoints reflect different stopping times, so their
distance ratio is not a matched-horizon performance metric. This is one arena and
one seed, not a navigation benchmark.

Generalization probes were executed, but the upstream protocol lacks a pre-training
baseline for every probe. Raw cross-odor output differences cannot establish a
clean quantitative generalization curve without that extra control. Likewise,
synaptic trace magnitude is not literally parameter-free: it depends on learning
rate, training history, activity threshold, and circuit choices even when readout
gain is one.

## First custom-plasticity experiment

`../scripts/temporal_pilot.py` adds online decaying eligibility and pooled PAM
activity traces to the same connectome circuit. The learning object only receives
spike counts and weights, not the stimulus schedule. It updates every 10 ms,
uses 100 ms eligibility decay and 50 ms dopamine decay, and has a fixed 4/s
depression coefficient. These are declared exploratory choices, not measured
fly constants. Weights remain bounded by multiplicative depression. There is
no LTP, compartment assignment, reward-prediction error, or consolidation.

Three pairings, seed 0:

| Condition | Rewarded-odor output suppression |
|---|---:|
| Simultaneous odor and PAM drive | 98.93% |
| Dopamine starts 100 ms after odor ends | 18.58% |
| Dopamine starts 1 second after odor ends | 0.30% |
| No external dopamine drive | 1.34% |
| Plasticity disabled | 1.07%; weights exactly unchanged |

Halving the plasticity update step to 5 ms retained strong paired suppression and
about 17.88% suppression with the 100 ms gap. Long-gap/no-drive output changes
were within roughly 1.5% of baseline. However, the tiny background weight drift
changed from about 0.006% to 0.061%: the rate threshold is sensitive to binning.
This must be fixed or characterized before treating the rule as numerically
converged. No external dopamine drive does not silence endogenous PAM spikes.

These observations establish a working temporal learning mechanism in this model.
They do not validate the chosen time constants or establish better behavior than
Daniel's rule. The schedules differ, only one pilot seed was run, and the custom
weights were not tested in navigation. The temporal gradient partly follows
directly from the imposed eligibility decay; it is an implementation check, not
an independent biological discovery.

## Proposed comparison before claiming improvement

Freeze odor sets, training counts, evaluation schedules, arena layouts, and all
readout/controller parameters before comparison. Compare original episodic LTD,
plasticity-off, temporal-only, compartment-only, and combined rules under the
same stimulation. Use separate development and held-out odor/seed sets.

Measure acquisition, discrimination, forward/backward timing, explicitly unpaired
reward, extinction, reversal, retention, and interference after learning a second
association. Record both synaptic/neural responses and behavior. Include
gain-sensitivity, silence/runaway checks, timestep tests, removal of eligibility
or dopamine, and anatomically matched shuffle controls where the claim concerns
connectome specificity. Counterbalance odor identities and source positions.

For navigation, keep source coordinates inaccessible to the neural learner and
controller; let only the evaluator use them. Replace privileged stopping with
sensory termination or a fixed test duration. Compare source occupancy and
choice probabilities over matched horizons, not just final distance.

**Recommended next objective:** reproduce a compartment-specific forward/backward
conditioning and reversal result with fixed physiological parameters. That would
address a genuine missing capability in Daniel's one-way episodic rule. A faster
or more attractive navigation video would be weaker evidence.
