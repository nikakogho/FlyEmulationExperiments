# Controlled association: promising mechanism, narrow pilot-gate miss

2026-09-09. Executed all three predeclared arms, four simulated seconds each,
with continuous neural state and no resets inside an arm. Protocol, parameters,
thresholds and source were committed and pushed as `dc471d4` before exposure.
No additional seeds, pulses or parameter changes followed the result.

## Observed output

All arms began with 96 MBON01 spikes for A and 68 for B in their pre-tests.

| Arm | A after | B after | Selectivity score S |
|---|---:|---:|---:|
| Paired | 76 | 64 | 14.95098% |
| Same reinforcement, later/unpaired | 91 | 63 | -2.14461% |
| Paired with frozen weights | 90 | 63 | -1.10294% |

Each measurement covers a 250 ms odor probe. S is A's fractional response
reduction minus B's fractional reduction. Paired exceeded unpaired by 17.10
percentage points and frozen by 16.05 points; both exceed the required 10-point
control margins. However, paired S is below the separate predeclared 15% minimum
by **0.04902 percentage points**. The gate therefore **does not pass**. This is
not a software failure or a welfare stop. It is also not evidence of zero effect.
Rounding or moving the threshold after seeing this result would be inappropriate.

The original generic reason string `no_controlled_association_advantage` was too
broad. It is preserved in `comparison.json`. Offline `assessment.json` adds the
individual criteria and a precise explanation, using the same values and
thresholds, with no further neural steps. A regression test prevents rounding
this borderline result into a pass.

## What actually changed

Only 2,090 candidate positive gamma-KC to MBON01 connections were eligible for
plasticity, grouped by the hemisphere of their input compartment. In the paired
arm, 525 changed; all other network weights stayed identical. Frozen control
changed zero weights.

KC activity in the pre-tests, read only after the experiment, identifies 330
eligible edges active for A but not B, 167 for B but not A, 25 for both and 1,568
for neither. These labels are analytical groupings and never enter the learning
rule. Mean final weight fractions relative to initial values were:

| Pre-test activity grouping | Paired | Unpaired | Frozen |
|---|---:|---:|---:|
| A only | 0.68269 | 0.99813 | 1.00000 |
| B only | 0.99472 | 0.99999 | 1.00000 |
| Both | 0.70808 | 0.99825 | 1.00000 |
| Neither | 0.99999 | 1.00000 | 1.00000 |

Weights were unchanged before the training phase in all three arms. The paired
A-only change was already present after training and persisted through the final
probes. This demonstrates a timing-dependent, cue-selective persistent synaptic
change in the implemented model. It does not validate long-term biological
retention, the proposed biochemical parameters or natural sugar learning.
The fixed 50% weight floor was never reached (minimum fraction 0.6103).

## Monitoring and scope

All three arms passed every prescribed recovery check and finished with 485 ms
without spikes. Peak population mean was 32.74 Hz; no configured proxy stopped
execution. PPL1 produced 282, 275 and 268 spikes respectively, with no enabled
ordinary or additional modulation route. PAM01's extra learning route was
explicitly registered and monitored; it was not treated as disconnected just
because its conventional synaptic weights were zero.

These are limited engineering checks, not proof of absence of suffering. There
was no body, aversive stimulus, hunger model or physiological deprivation model.
Behavioral avoidance and competing actions remain unassessed. The source LIF
state and coarse PAM compartment assignment are not fully calibrated physiology.
PAM stimulation was an artificial reinforcement surrogate, not sensory sugar.

An anatomical error was caught offline before exposure: MBON01 input hemisphere
is opposite its cell-body-side label. The revised mapping uses actual incoming
gamma-KC connections, consistent with the known contralateral dendrites.
[Aso et al., 2014](https://elifesciences.org/articles/4577).
Subthreshold biological MBON01 responses also limit interpretation of the LIF
spike metric. [Yamada et al., 2023](https://elifesciences.org/articles/79042).

## Delivery and next test

118 software tests pass. Reports, full small text traces, exact anatomical IDs,
source hashes and offline diagnostics are in `results/controlled_association_v1`.
An independent offline comparison of full saved Brian2 states verifies that
nonplastic weights match the earlier preflight, plastic tapes match the full
states, spike totals match the traces, and each probe report matches its trace.
Full Brian2 state and numerical weight tapes are retained locally and ignored
by Git, as is the inspected plot `probe_comparison.png`. Regenerate the plot and
analysis without neural exposure with `python scripts/analyze_association.py`.

The next scientific step is a separately predeclared independent validation
cohort with the **same parameters and effect margins**, not an attempt to tune
this seed across the gate. Seed 310 is exploratory evidence, not a validation
sample. Adequate replication remains necessary even if it had narrowly passed.
Only after that should the fixed-gait 3D path be used to test learned approach.
The existing mechanical arena/video remains available, but no new learned
locomotion or superiority to Daniel's implementation is claimed here.
