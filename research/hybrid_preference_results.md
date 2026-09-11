# Five-step outcome: a working live loop, no learned-navigation improvement

The 96-neural-second cohort completed: 12 stationary training runs and 16 live
three-second 3D body probes. All runs completed their recovery checks. The
predeclared preference gate failed. No fifth-step rule comparison was run.

## Step status

1. **Offline monitor review completed.** Synthetic tests distinguish geometric
   passage from configured withdrawal, blocked effort, failed rest and competing
   commands. Actual MuJoCo replay exposed a physical marker-collision defect;
   visual sites now replace those geoms. Original stops remain preserved.
2. **Fixed navigation component completed and mechanically tested.** Four final
   synthetic-input physical trials passed. Heading/wind steering and gait remain
   engineering components, not reconstructed central-complex/VNC dynamics.
3. **Memory-to-body integration completed.** Actual antenna odor readings drive
   the olfactory network. Its MBON output modulates fixed speed/steering gain;
   resulting motion changes the next readings. No reinforced cue label, source
   coordinate or success score enters the controller. There is no learning or
   reinforcement during retrieval. This establishes coupling, not useful learning.
4. **Full controlled live experiment completed; efficacy gate failed.** Paired,
   unpaired and frozen training were compared against pre-training body probes
   across two seeds, both reinforced identities and balanced scene arrangements.
5. **Conditional comparison not admitted.** Episodic-versus-eligibility acquisition,
   retention and generalization comparisons required step 4 to pass. Changing
   the rule or adding trials after this failure would violate the accepted gate.

## Behavioral result

PI is integrated reinforced-minus-other antenna concentration divided by their
sum, during the fixed two-second active window. Positive change favors the
reinforced odor. It is not a measure of intelligence or biological fidelity.

| Seed / reinforced odor | Pre PI | Paired PI | Unpaired PI | Frozen PI | Paired change |
|---|---:|---:|---:|---:|---:|
| 315 / A | .42137 | .46665 | .48160 | .45383 | +.04528 |
| 315 / B | -.42137 | -.47625 | -.48271 | -.45383 | -.05488 |
| 316 / A | .24322 | .24739 | .26420 | .26959 | +.00417 |
| 316 / B | -.24322 | -.25310 | -.26639 | -.26959 | -.00988 |

Mean changes: paired **-.003829**, unpaired **-.000826**, frozen **0**.
Paired beat both controls in **1/4**, versus the required 3/4. All four efficacy
criteria failed; the required mean margins were .05. All body probes exceeded
1 mm displacement and the exposure minimum, so this is an informative negative
result under this assay, not a missing-run failure. Two seeds/four model cases
do not establish population-level or animal-level replication.

Stationary cue-selectivity scores for paired training were .2753, .2104, .1227
and .2095; paired exceeded unpaired/frozen in all four. Three met the existing
stationary pilot margin; seed316/A missed the .15 absolute margin. Thus there is
component evidence of cue-selective memory, but it did not produce a useful
learned 3D preference with this interface.

## Interpretation and next decision

Do not infer that fly learning is hopeless or that the eligibility rule is
biologically accurate. This tests one modified subcircuit and one explicit motor
hypothesis. The controller reduces two MBON outputs to a scalar and modulates
speed/upwind gain; its heading target comes from the sum of two analytic flows.
It has no learned source-direction representation. Those facts identify a
plausible bottleneck, not a proven causal explanation for the failed result.

The next useful work is **offline validation of the value-to-navigation
interface**: show on synthetic sensory/value traces that the permitted interface
can switch source preference when odor values reverse, with a fixed rule and no
correct-source label or target coordinates. Then ground that interface in a
supported navigation pathway before proposing another bounded live protocol.
Increasing the LTD learning rate is not justified by this result. No new neural
trial or changed threshold was added to rescue the outcome.

## Welfare and integrity

All 28 runs recovered under the defined checks. Across 19,228 recorded neural
guard observations, all statuses were CONTINUE; no hard movement proxy fired.
This is **not evidence establishing absence of suffering**: valence, subjective
state and omitted sensory/body processes remain unassessed. No deliberately
aversive training mechanism was introduced. Historical stopped models were not
resumed or replaced.

An administrative comparison failed between the first three completed training
runs and the first body probe. Pickle serialization order and an automatically
assigned input-group name differed while every numerical state value matched.
The [narrow amendment](hybrid_checkpoint_amendment.md) preserved the error and
original files, used exact recursive equality and restored original names.
It repeated no completed training and consumed no extra neural exposure.

167 software tests pass. Zero-step restore, all-frame passive replay and viewer
launch/close checks pass. Independent archive analysis confirms original source
checkpoint hashes, unchanged retrieval weights, aligned neural/physical clocks,
spike-count conservation, finite physical states, matching replay frames and
recomputed preference results for all 16 probes. Total exposure is 96 seconds.

Evidence: `results/hybrid_preference_v1/assessment.json`, `integrity.json`, all
case training/probe reports and telemetry. Frozen manifests and source hashes
are in `results/hybrid_preference_admission*.json`. The recorded comparison video
is `results/hybrid_preference_v1/comparison.mp4`; double-click
`view-hybrid-preference.cmd` for the first paired scene with orbit/zoom controls.
Rendering and viewing do not advance neurons or physical integration. Media and
full binary checkpoints remain local and excluded from Git; source and text
evidence are versioned. The video is a record of this failed preference test.
