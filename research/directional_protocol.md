# Directional interface protocol, 2026-09-10

Conditional on independent association validation passing, six naive fixed-circuit
assays (seed 311, A/B each with center/left/right drive), each one simulated
second. Total six seconds. No reinforcement, plasticity, body, physiological
needs or aversive stimuli. Use the same modified olfactory circuit, fixed-weight
pathway audit, population activity limit, finite-data checks and 5 ms cadence.
Any stop cancels remaining assays. No automatic retry or sign/gain search.

Each assay: 0–.25 quiet, .25–.50 odor, .50–1.00 recovery. At the end require
50 ms quiet. One-sided normalized concentration 1 on that antenna and palp;
center concentration .5 on both sides. Mapping uses actual anatomical AN versus
MxLbN nerves and side labels. Unknown side is an explicitly recorded bilateral
mean approximation, not assigned a made-up direction. Rates remain 500 Hz times
normalized concentration, not measured ORN firing. Coverage limits of the
stationary preflight remain: no behavioral or subjective-welfare inference.

Output order is the MBON01 gamma-input hemisphere from graph audit. For each
odor, divide the left and right output counts by their corresponding center
counts, then D=(L-R)/(L+R). Require both center outputs >=5 spikes, D>.10 for
left-only stimulation and D<-.10 for right-only stimulation. These margins are
engineering direction-discrimination tests, not physiological fits. Failure
means this interface cannot support the proposed bilateral steering as tested;
do not flip signs or calibrate on a desired navigation trajectory.

Only concentration/time cross the sensory bridge. The rule and future motor
readout receive no source coordinates. The exact source positions are available
to the arena and offline scorer only. No full 3D neural run is covered by this
protocol; embodiment needs its own bounded behavioral-monitor review.
