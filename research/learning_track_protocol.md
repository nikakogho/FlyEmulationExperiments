# Independent learning track: bounded olfactory preflight

2026-09-09. The user authorized separating the learning demo from motor-accuracy
research. The fixed StandingController is the eventual motor interface; its
parameters do not depend on training condition or cue position. The failed
leg-calcium model is not a prerequisite for this track and is not used here.

First assay: one stationary, continuous olfactory-subcircuit preflight, seed 310.
No body is instantiated in this first assay. Quiet baseline 0-0.25 s, odor A
0.25-0.50 s at the existing upstream 500 Hz external Poisson setting, then drive
removed until 1.0 s. These rates are upstream engineering inputs, not measured
receptor firing. No reward, learning, repeated trials, resets or replicas in this
preflight. Membrane states remain continuous across stimulus boundaries.

Active circuit: the existing pinned olfactory/AL/KC/APL/MBON/PAM/PPL1 subnet,
with the upstream documented connectivity edits unchanged. Sensory input goes to
anatomically labelled ORNs through the existing class assignment. No direct
visual-KC input, image conversion, source position or task label is supplied.
Readout is the anatomically identified MBON01 population, not pooled MBONs with
potentially different behavioral roles. This is not yet a validated motor sign
or a full-organism upload. Static metadata records exact output and plastic IDs.

The candidate learning interface permits only positive KC-to-MBON01 weights and
PAM01 modulation, a coarse gamma5 assignment. Fine compartment assignment remains
unvalidated, so biological accuracy is not claimed. It is not exercised during
this first exposure. Future training/test exposure requires its own explicit
protocol after inspection of this preflight.

Guard coverage: inspect before every 5 ms neural block, plus a terminal check.
Read all membrane/synaptic states for finiteness, recorded group spike counts,
clock consistency, actual external input, and expected zero reward. Model needs,
hunger, pain and homeostasis are not implemented; their absence is not a comfort
assessment. Aversive-pathway recruitment is conservatively operationalized as
any PPL1 spike since the previous observation and stops immediately. Total mean
population rate above 150 Hz for 50 ms also stops. These are predeclared
engineering exposure limits, not validated suffering thresholds.

Stationary rest means removal of sensory drive is available without forced
actuation; there is no body constraint or requested physical effort in this
assay. After removal, any spike activity continuing at the final check is a
failed recovery screen. Behavioral avoidance and competing actions cannot be
assessed without a body, so they are explicitly outside this stationary assay;
they must be instrumented before embodied execution. No claim of complete
welfare coverage follows from this preflight.

On a stop, latch and save; no additional neural step, automatic restart, drive
increase, alternative seed or replacement circuit. Inspect the stopped trace
offline. The one-second budget prevents further simulation. Synthetic tests of
the guard run before this assay. Passing only supports considering the next
bounded protocol, not launching legacy unguarded learning/embodied scripts.
