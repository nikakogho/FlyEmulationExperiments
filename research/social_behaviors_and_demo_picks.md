# Fly social behavior and the three next demonstration picks

Research and local source audit: 2026-09-08. Recommendations, not newly run
demonstrations. Scope is adult Drosophila melanogaster, not every fly species.

**Updated user constraint:** prioritize avoiding possible distress. Threat,
punishment, fighting, deprivation and injury demonstrations below are no longer
on the active agenda. First address coherent sensory feedback and rest-capable
control. See [sensory coherence and welfare](sensory_coherence_and_welfare.md).
The inventory below documents biological possibilities, not a commitment to
implement every paradigm.

## Recommendation

Prioritize **learned odor approach/avoidance**, **visual following of another
fly**, and **optomotor turning**. These cover memory, a social-looking interaction,
and an innate visual reflex without requiring fighting, flight, or mating
biomechanics. Looming-triggered freezing/fleeing and pheromone aggregation are
the strongest next extensions.

The current 8,991-neuron olfactory/mushroom-body subnetwork cannot be expected
to produce all fly behavior. It lacks complete visual, social, descending and
body-control circuits. A fixed gait is a declared motor abstraction; a rule that
chooses the target, recognizes a mate or decides to fight is a behavioral model.
Both can be useful, but they support different claims.

“Natural” should mean that modeled sensory input and internal neural state
generate the response, with the external controller denied the answer. It does
not mean omitting biologically necessary innate circuitry. In particular,
phototaxis and optomotor responses need not be learned within the experiment.

## Top three, ranked for this project

Cost and difficulty are engineering judgments, not measured benchmarks of these
unimplemented extensions. Costs assume one articulated responding fly on flat
ground. Visual overlays may help the human observer but must not change what the
fly senses.

| Priority | Proposed 3D scene | Compute | Simulation/integration difficulty | Online learning difficulty | Visual clarity |
|---|---|---|---|---|---|
| 1 | Two odor patches: acquire a preference or avoidance, move the patches, then reverse the contingency | Low added sensory cost; many training/test episodes make total cost medium/high | Medium/high: repair reward exposure and downstream output interpretation | Highest of the three; acquisition first, reversal later | High with source labels, trajectory trails and a preference graph |
| 2 | A responding fly follows another fly around turns, then loses it behind an occluder | Medium/high: additional visual-network inference; passive leader avoids a second autonomous brain | Medium: existing FlyGym example, but dependencies, checkpoints and calibration needed | None for initial reproduction; published components are already fitted | Very high |
| 3 | Striped arena walls rotate clockwise/counterclockwise; the fly changes its turning with visual motion | Medium with the same visual model; short trials and one body | Medium: motion-to-turn pathway and readout still need validation | None: innate sensorimotor response | High; clear reversal of walking curvature when the scene reverses |

### 1. Learned odor approach/avoidance: best for the primary plasticity question

Start with one appetitive acquisition protocol and reward-free choice tests.
Add aversive learning and reversal only after acquisition works. A rule that
only depresses one set of weights does not automatically support all three.
Counterbalance odor identities and positions. Use local food contact rather
than distance-shaped reward, and ensure the arena provides repeated encounters.
Training exposure is experimental design, not cheating; forcing the answer into
the navigation controller would be.

The strongest new lead is **UpWind Neurons (UpWiNs)**: experiments identify
downstream neurons that integrate opposing MBON inputs and help express learned
odor value as upwind movement. This gives us a biologically motivated route to
investigate instead of pooling all MBON types into one avoidance signal. It
requires anatomical mapping and a local wind-sensing model; it is not a ready
drop-in solution. [Aso et al., 2023](https://elifesciences.org/articles/85756).

Reversal has specific dopamine/compartment mechanisms; do not implement it by
manually swapping the stored preference. [Reversal-learning study, 2021](https://www.nature.com/articles/s41467-021-21388-w).

Pass criteria: retained reward-free choice exceeds frozen and unpaired controls,
follows odor identity after relocation, and later changes appropriately after
reversal. Include dopamine/pathway disruption and preserved baseline responses.

### 2. Following: best immediate social-looking result

NeuroMechFly v2 demonstrates following with a connectome-constrained visual
network. This substantially reduces integration uncertainty compared with
inventing a new social circuit. [Wang-Chen et al., 2024](https://www.nature.com/articles/s41592-024-02497-y).

The installed FlyGym 1.2.1 source was inspected, not executed for this task:

- `examples/vision/arena.py`: the leader's position is imposed along a circular
  path. It is not an independently motivated fly.
- `examples/vision/follow_fly_closed_loop.py`: visual-neuron deviations from
  baseline define an object mask; an explicit turning rule drives the gait.
- `examples/vision/vision_network.py`: wraps FlyVis and currently sets the device
  to CPU. The closed-loop implementation consumes one frame at a time.
- `examples/vision/realistic_vision.py`: loads a fitted visual-network checkpoint
  and converts the visual channels to grayscale.
- The example uses 500 Hz vision. Our light pilot used 10 Hz. Neither its cost
  nor its temporal accuracy can be inferred from the old light run.
- `torch` and `flyvis` are absent from the current `.venv`; additional setup and
  checkpoint availability checks are needed. No claim of local reproduction.

The visual model itself was optimized subject to connectome constraints; it is
not evidence of learning a social skill spontaneously during the demo.
[Lappalainen et al., 2024](https://www.nature.com/articles/s41586-024-07939-3).

Pass criteria: unseen leader paths, stationary target, same-size non-fly object,
occlusion, contrast manipulation, and visual-pathway ablation. A follower that
also follows a ball demonstrates object tracking, not social recognition.
After this baseline, replace the passive leader with a second autonomous agent.

### 3. Optomotor turning: best short visual-circuit check

Moving panoramic patterns can elicit compensatory turning. Motion-sensitive
bilateral circuits offer a concrete physiological target. The response is
distinct from chasing a bright point, and an innate response is not a failure
to learn. [Bilateral optic-flow study, 2024](https://www.nature.com/articles/s41467-024-53173-w).

Reuse the visual-network integration, then constrain the downstream readout
using independent stimulus-response data. Do not feed the controller the wall's
rotation command. Compare clockwise, counterclockwise, stationary and uniform
brightness conditions; test contrast/speed dependence and neural silencing.
Pass criteria concern response direction and tuning, not a visually plausible
turn alone. This supplies a useful foundation for later looming detection.

## Real social/group behavior: what transfers and what does not

| Behavior observed in real flies | Feasibility in our simulation | Biological source |
|---|---|---|
| Courtship pursuit and visual tracking | Following is accessible as a component; mate recognition and courtship motivation need additional state-dependent circuitry | [LC10a and arousal](https://www.nature.com/articles/s41586-021-03714-w) |
| Courtship tapping, wing song and mating decisions | Poor first target: sex-specific circuits, contact chemistry, hearing and wing/body motor programs are missing. Our female-derived subnetwork is not a male courtship brain | [Song circuitry](https://www.nature.com/articles/s41593-024-01738-9) |
| Aggregation at socially marked food | Promising olfactory extension: model emitted/deposited chemical cues and validated receptor-to-action pathways. Several flies independently visiting ordinary food is not enough to establish social attraction | [9-tricosene, Or7a/DL5](https://pubmed.ncbi.nlm.nih.gov/26422512/) |
| Social approach and preferred spacing | Both same- and opposite-sex interactions are relevant. Requires recognition and state mechanisms absent from our synthetic color-KC interface; serotonin matters in the studied behavior | [Sun et al., 2020](https://www.nature.com/articles/s41467-020-19102-3) |
| Clusters formed through encounters | Attractive group scene, but tarsal sensation, vision, contact and stopping/restarting dynamics need modeling. A proximity-stop rule would supply the behavior externally | [Jiang et al., 2020](https://elifesciences.org/articles/51921) |
| Touch-triggered collective escape cascades | Visually excellent but relatively expensive: multiple bodies, appendage contact, mechanosensory transduction and motor responses | [Ramdya et al., 2015](https://pmc.ncbi.nlm.nih.gov/articles/PMC4359906/) |
| Safety in numbers after a threat | Neighbors' motion can help frozen flies resume moving; LC11 is implicated. One focal fly and replayed neighbors is a cheaper first assay, not a mutually interacting group | [Ferreira and Moita, 2020](https://www.nature.com/articles/s41467-020-17856-4) |
| Aggression and effects of winning/losing | Full fighting is a poor first target: opponent recognition, aggressive states and lunge/fencing biomechanics. An odor associated with an adverse encounter is a narrower learning target | [Kim et al., 2018](https://pmc.ncbi.nlm.nih.gov/articles/PMC5798363/) |
| Mate copying/social learning | Real experimental phenomenon, but low current feasibility: requires parsing observed interactions and generating an internal learning signal. Rewarding a hard-coded “successful mating observed” label would assume the key computation | [Monier et al., 2019](https://pmc.ncbi.nlm.nih.gov/articles/PMC6333735/) |
| Socially influenced egg-site choice | Chemical site selection is approachable; reproductive state and actual egg laying are separate missing mechanisms. Preference need not increase monotonically with pheromone concentration | [Cazalé-Debat et al., 2023](https://pmc.ncbi.nlm.nih.gov/articles/PMC10027874/) |

These are courtship and social interactions; they do not establish human-like
romantic attachment. None of the listed social behaviors is currently validated
as an emergent behavior of our 8,991-neuron simulation.

## More real effects worth keeping on the list

- **Looming threat: freeze versus run.** A growing dark disk is visually clear
  and cheap to render. Defensive responses depend on behavioral state; jumping
  and flying add unnecessary motor difficulty initially. Requires new visual
  and descending circuitry. [Zacarias et al., 2018](https://www.nature.com/articles/s41467-018-05875-1).
- **Social release from freezing.** Add moving neighbors only after the solitary
  response is validated; compare fly-shaped and matched nonsocial motion.
- **Odor-plume search and reacquisition.** Intermittent odor and local wind cues
  can generate searching rather than smooth gradient following. FlyGym includes
  a bio-inspired behavioral controller; label that separately from a neural
  reproduction. [Walking odor navigation](https://elifesciences.org/articles/37815).
- **Phototaxis/light preference.** Still worth testing, but not automatically a
  learned preference: adult walking photopreference depends on state, including
  flight ability. Our failure to learn a food-associated color does not test all
  natural phototaxis circuitry. [Gorostiza et al., 2016](https://doi.org/10.1098/rsob.160229).
- **Extinction, reversal and interference between memories.** Good extensions
  once acquisition is robust, because they distinguish a useful plasticity rule
  from irreversible weight suppression. [Incentive-circuit model and experiments](https://elifesciences.org/articles/75611).
- **Sequential grooming after dust stimulation.** A real suppression hierarchy
  makes it compelling visually, but body-part sensing and grooming motor
  programs must be added. [Seeds et al., 2014](https://elifesciences.org/articles/02951).
- **Taste-triggered feeding or antennal grooming responses.** The larger Shiu
  model supplies neural validation targets; this does not make our walking gait
  perform proboscis extension or cleaning automatically. [Shiu et al., 2024](https://www.nature.com/articles/s41586-024-07763-9).

## Compute and what counts as success

Our measured last batch took 52–140 wall seconds per 2.4-second trajectory
(median 117 seconds, with concurrent processes). This is a local workload
measurement, not the speed of the proposed visual-network demos. Body physics
and sensing are substantial costs; RTX availability does not make all of this
GPU accelerated. Start with one focal body, then two interacting agents.

Use inexpensive circuit/stimulus tests to reject bad parameters before long 3D
trials. Use replayed neighbors for controlled sensory experiments when useful,
and disclose that they are not independent agents. Keep difficult obstacles out
until behavior works on a flat floor. Preserve failures and test held-out
conditions. Behavioral similarity, circuit fidelity and enhanced learning are
three different outcomes; a convincing movie establishes none by itself.
