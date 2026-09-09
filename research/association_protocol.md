# Controlled association pilot v1 — declared before exposure

2026-09-09. Following the successful fixed-circuit sensory preflight and the
user's instruction to continue, run one three-arm stationary pilot, seed 310
in each arm. Arms are paired, temporally unpaired, and frozen plasticity, in
that fixed order. These are prospectively defined experimental controls, not
replacement replicas after a stop. Maximum exposure is four simulated seconds
per arm, twelve total. Any welfare/execution stop cancels remaining arms. A
negative learning contrast is reported without retuning or additional seeds.

## Circuit and scientific claim

Retain the exact modified 8,991-neuron olfactory circuit and upstream source
hashes from preflight v2. No hunger, pain, deprivation, threat, punishment,
homeostatic need or body is implemented. No motor commands or blocked physical
effort occur. Behavioral avoidance/competing-action coverage remains unassessed
until embodiment. Removal of drive is available in each quiet interval.

Enable only positive, same-hemisphere KCg-* to MBON01 edges for depression.
Modulation comes from actual spikes of PAM01 neurons on the corresponding
side. This narrows the previous all-KC candidate to a coarse gamma5 pathway;
precise local release fields and receptor dynamics remain unvalidated.
Input hemisphere is determined from actual incoming gamma-KC edges, not MBON
cell-side annotation: MBON01 has contralateral dendrites. Static inspection
found 1,154 left-gamma inputs to the right-labelled MBON01 and 936 right-gamma
inputs to the left-labelled cell, with no gamma input from the other side.
This agrees with [Aso et al., 2014](https://elifesciences.org/articles/4577).
PAM01 grouping still uses its coarse side annotation; PAM-to-KC graph edges
include cross-side contacts, so this is an explicitly simplified compartment
model, not a reconstruction of each dopamine release field. The first static
audit rejected the incorrect same-cell-side assumption at zero neural steps;
the input-compartment correction was made before any exposure or outcome data.
PPL1 and PAM conventional outputs remain zero as in the upstream model.
PAM01 now has an explicit additional pathway through the plasticity update;
PPL1 has no implemented plasticity or other modulation route. Zero conventional
weights are not used to conceal that newly enabled PAM function.

The existing compartment-local candidate LTD rule is used, with fixed dt=5 ms,
eligibility decay 100 ms, dopamine-signal decay 50 ms and eta=4/s. KC spiking
sets eligibility to one; otherwise it decays. The local mean PAM spike rate,
normalized by 60 Hz, drives the filtered modulator (existing 1 Hz drive cutoff).
Weights decrease multiplicatively with eligibility times modulation, bounded
at 50% of initial strength. No potentiation, negative weight, or unrelated edge
write is allowed. These are retained engineering parameters, not physiology fits.

The rule receives spike counts and local weights only. It never receives odor
identity, desired response, source coordinates or the external reward flag.
It runs continuously, including during probes and recovery. Thus endogenous PAM
activity can also cause learning; controls must detect nonspecific effects.
Frozen control advances traces but never changes weights. No membrane resets,
legacy episodic training or hidden learned steering controller are used.

An external PAM01 Poisson pulse at 60 Hz is an artificial reinforcement surrogate,
not simulated sugar tasting or evidence of natural reward processing. External
odor drive is the prior 500 Hz setting; neither is calibrated receptor firing.
The source LIF state is not a faithful somatic-voltage prediction.

## Schedule (seconds; half-open input intervals)

| Time | All arms | Paired/frozen PAM01 | Unpaired PAM01 |
|---|---|---|---|
| 0–0.25 | Quiet | Off | Off |
| 0.25–0.50 | Pre-test A | Off | Off |
| 0.75–1.00 | Pre-test B | Off | Off |
| 1.25–1.50 | Training A | On 1.35–1.50 | Off |
| 1.95–2.10 | No odor | Off | On |
| 2.75–3.00 | Post-test A | Off | Off |
| 3.25–3.50 | Post-test B | Off | Off |
| All other intervals through 4.00 | Quiet | Off | Off |

Nominal pulse duration/dose and sensory exposure match across arms. Stochastic
realized spikes can differ. Same seed and apparatus schedule control some noise;
one seed is not population replication. Counts at t describe the previous 5 ms;
reported input rates at t describe the next interval.

## Monitoring and stopping

Before every 5 ms neural step, inspect measured counts, v/g finiteness, actual
external rates against the schedule, clock, full synaptic source/target/weight
arrays and the declared modulation inventory. Verify actual weights against an
expected copy. Authorize only the candidate rule's bounded named-edge changes;
all other mutations or inventory changes stop. Any PPL1 spike with an enabled
ordinary/additional route stops; disconnected spikes remain visible in logs.
Activity above a mean 150 Hz for 50 ms stops, unchanged from preflight. These
are engineering proxies, not validated suffering thresholds.

Require the last 50 ms to be spike-free at t=0.75,1.25,1.95,2.75,3.25,4.00 before
allowing the next phase or accepting completion. This checks recovery after
each exposure, including the unpaired modulator. Do not extend a failed window.
On stop, preserve full Brian2 state and telemetry; no correction, restore,
automatic retry, stimulus increase or alternative seed. Passing these checks
does not establish comfort or cover every potentially adverse dynamic.

## Prospective interpretation

Primary readout: MBON01 spike counts during the four 250 ms probe intervals.
Require pre-A and pre-B counts >=20 in every completed arm. For each arm compute
S=(preA-postA)/preA - (preB-postB)/preB. The exploratory gate requires paired
S>=0.15 and paired S exceeding both unpaired and frozen S by >=0.10. All arms
must complete with recovery. These are predeclared engineering effect margins,
not significance tests or biologically measured success thresholds.

A pass supports a candidate neural association in this modified model. It does
not establish natural reward learning, 3D approach, improved biological accuracy,
superiority to Daniel's implementation, or generalization across flies/seeds.
A failure leaves the mechanism/result visible and calls for offline diagnosis.
Retain nonplastic-weight checks, weight snapshots and probe KC counts to inspect
locality and cue overlap without further neural exposure.

Compartment-dependent learning is supported by
[Aso and Rubin, 2016](https://elifesciences.org/articles/16135).
The gamma5/beta-prime2a literature also reports predominantly subthreshold
MBON responses, so an LIF spike-count assay is an abstraction, not replication
of that electrophysiology:
[Yamada et al., 2023](https://elifesciences.org/articles/79042).
