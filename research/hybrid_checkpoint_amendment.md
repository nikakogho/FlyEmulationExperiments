# Administrative checkpoint amendment — before the first live body probe

All first-case training arms completed their4s schedules with recovery. The
runner then stopped BETWEEN runs because pre-checkpoint pickle bytes differed.
Offline inspection found an automatically assigned Brian2 group name,
`poissongroup` versus `poissongroup_1`, and serialization ordering. The full
pre-training numerical state was identical: neuron and synapse arrays, input
rates, counters, RNG, queues and clocks. No neural/behavioral guard fired.

Replace byte identity with exact recursive state equality after normalizing ONLY
the single recognized PoissonGroup name. All arrays retain dtype/shape/value
checks; no dynamics, weights, RNG state or queues are omitted. Tests reject
voltage, clock, queue, RNG, dtype and input-group-count changes. Body construction
now explicitly uses the original checkpoint's input-group name so Brian can
restore its original file directly; checkpoint files are not rewritten.

Continue only the already-planned, not-yet-started probes and remaining cases.
Do not repeat the three completed training runs or exceed the original96s total.
The original error, admission manifest and interruption assessment are retained.
Resumption code admits ONLY this exact between-run error with three completed,
recovered training arms and zero body probes, and refuses any neural guard stop.
It permits one bookkeeping resumption; it cannot resume a stopped neural model.

The circuit, controller, monitor, fields, exposure windows, identities, cases
and outcome gates are unchanged. This corrects an implementation-level equality
test, not an experimental outcome or safety threshold. The user's authorization
to complete all five steps includes repairing this routine bookkeeping failure.
Record the amended source hashes in `hybrid_preference_admission_v2.json` before
continuing. The original byte-identity sentence is superseded only as above.
