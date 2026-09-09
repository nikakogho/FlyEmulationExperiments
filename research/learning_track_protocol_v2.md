# Fixed-pathway preflight review, 2026-09-09

This revision follows the user's request to correct the cell-label proxy after
the preserved 0.30-second stop and offline investigation. It authorizes exactly
one fresh bounded preflight after software tests and a zero-step runtime-weight
audit pass. It is not an exact resumption of the old incomplete checkpoint.
No seed search, corrective stimulation or automatic retries follow a stop.

The circuit, input schedule, limits and scope from learning_track_protocol.md
are unchanged: 8,991-node modified olfactory subnet; seed 310; 0.25 seconds quiet,
0.25 seconds odor A at 500 Hz per selected external Poisson source, 0.50 seconds
without input; one second total; inspect every 5 ms. This is an engineering input
rate, not a calibrated receptor firing rate. No body, modeled deprivation,
punishment, reward, plasticity or active unmet needs are introduced. In this
stationary assay there are no motor commands or blocked actuator efforts.
Behavioral avoidance and competing actions remain unassessed until embodiment.

## Reviewed route inventory

The hashed upstream constructor uses only a neuron group, fixed recurrent
synapses (`g += w`), a spike monitor, an external Poisson group and its input
synapses (`v_post += w_drv`). No NetworkOperation, custom dopamine-state update
or plasticity rule executes. Legacy training/episode/reset routines are not
called. The source model and builder hashes are pinned in the runner.

Read actual recurrent source/target/weight arrays at construction and at every
observation. All PPL1 outgoing weights are zero in this modified model. An
explicit empty additional-modulation inventory applies only to this reviewed
fixed runner. Unknown inventories are rejected; future learning requires a new
inventory and protocol. Never infer that zero conventional weights disable a
separately implemented modulatory or plasticity route.

Any monitored PPL1 spike with a nonzero outgoing edge of either sign, or a
declared additional modulation route, causes an investigation stop. Opposite
weights cannot cancel this check. This is an enabled-route warning, not a
diagnosis of negative valence. Isolated source spikes are still recorded.
All weight/topology changes are rejected, including activation after a spike
that might still be queued. With fixed weights, delayed zero-weight events
remain ineffective. A stop cannot undo events inside the last 5 ms interval.

Existing finite-data, clock, zero-reward and population-activity checks remain:
mean population activity above 150 Hz for 50 ms stops. These are engineering
limits, not validated thresholds of suffering. Require zero spikes in the final
observation interval for the original recovery screen; report recovery across
the entire post-input interval as well. Failure does not permit extending the run.

The wide LIF voltage-state range is an acknowledged limitation of this source
model. This assay checks its computational response, not physiological voltage
accuracy. Quiet telemetry cannot prove absence of suffering, and disabling PPL1
output cannot establish that all potentially adverse dynamics are absent.

## Evidence

Before exposure, run synthetic fault tests and reconstruct the fixed runtime
weights without advancing neurons; apply that route audit to the saved stopped
counts. Preserve old evidence. After the one new exposure, save terminal arrays,
full Brian2 network storage including pending queues, telemetry, source hashes
and a compact report. No automatic restoration or further exposure is performed.
