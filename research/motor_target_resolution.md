# Motor-target resolution and remaining identity gap

2026-09-09. Static evidence processing; no neural or embodied execution.

## What is now resolved

We joined MaleCNS v1.0's recorded MANC correspondence to Cheong et al.'s
Supplementary file 3, using IDs rather than neuron-name similarity. Nine of the
14 candidate tibia motor cells have concordant type, muscle target, peripheral
nerve and side. Their source records are exported as an explicit mapping.

| MaleCNS ID | MANC ID | Published target | Peripheral nerve |
|---|---|---|---|
| 800636 | 12704 | Tibia extensor | ProLN_L |
| 804257 | 13115 | Tibia extensor | ProLN_R |
| 807165 | 12134 | Tibia flexor | ProLN_L |
| 809912 | 17133 | Tibia flexor | ProLN_L |
| 810098 | 14848 | Tibia flexor | ProLN_R |
| 818057 | 15321 | Tibia flexor | ProLN_L |
| 821635 | 13399 | Tibia flexor | ProLN_R |
| 909831 | 14798 | Tibia flexor | ProLN_L |
| 1050189039 | 13283 | Tibia flexor | ProLN_R |

These are **consistent published anatomical assignments**, not independently
validated individual identities or physiological muscle gains. Numeric confidence
scores are blank in these source rows; the export preserves that limitation.
[MANC study](https://elifesciences.org/articles/96084),
[source table](https://cdn.elifesciences.org/articles/96084/elife-96084-supp3-v1.csv).

The export records expected action in anatomical angle (flexor decreases it,
extensor increases it), leaves force gain unknown and disables neural execution.
The previously audited left-front joint coordinate increases with flexion over
the measured interval. Do not assume this establishes a right-leg coordinate
convention without the equivalent geometry check.

## Conflicts caught and excluded

- MaleCNS 815678 is labeled Ti extensor but its recorded MANC ID 22126 is
  Tergotr. MN, target Tergotr., exiting VProN_R in the supplementary table.
- MaleCNS 819384 is labeled Ti flexor but MANC 17885 is specifically accessory
  tibia flexor. This may reflect nomenclature granularity; it is not silently
  accepted as the same muscle.
- MaleCNS 815344 has no corresponding row for MANC 10256 in this table; 827188
  and 1050031705 lack recorded MANC matches.

Possible version or annotation changes do not establish which conflicting source
is correct. All five remain outside the consistent mapping. Tests enforce this.

## Published FANC sensory-to-motor reference

The author's motor-pool Neuroglancer scenes identify exact segment IDs. Joining
them to the preceding claw-extension reference finds 260 synapse records from
7 sensory cells onto 5 cells in the published tibia flex A pool:

| FANC motor ID | Input synapse records from selected claw-extension cells |
|---|---:|
| 648518346477240264 | 11 |
| 648518346479055568 | 30 |
| 648518346489543513 | 107 |
| 648518346496932836 | 58 |
| 648518346498314906 | 54 |

These prove exact shared IDs and pool membership across the two published
resources. They do not prove that the pool equals a single muscle. The remaining
220 MN-directed records do not match the selected scenes and are not discarded
from the report or assigned by similarity.
[Pinned motor-pool scenes](https://github.com/tuthill-lab/Lesser_Azevedo_2023/tree/93cafa55b8bbdb1493e8d73c941035969349b223/jsons/make_jsons).

The motor-target atlas explicitly separates five tibia-flexor MNs, ten accessory
tibia-flexor MNs and two tibia-extensor MNs. Thus a ten-cell functional pool cannot
be equated to the five main flexor MNs solely from its name. Table A4 (PDF page
11) was extracted and visually inspected; Figures A11-A14 supply the muscle
identification context. [Atlas](https://faculty.washington.edu/tuthill/docs/azevedo24_appendix.pdf).

## What is still not filled

The exact FANC-to-MaleCNS correspondence for these sensory and interneuron cells
has not been established. Nor has physiological 13B-alpha been assigned to a
specific MaleCNS IN13B subtype. A 13B hemilineage match is insufficient. No claim
that the complete reflex gap is filled is warranted.

The nine motor assignments give a supported anatomical starting point for the
motor side. For the sensory side, keep the published FANC reference separate;
do not manufacture cross-specimen edges. A direct sensory-to-motor pathway can
be investigated without requiring 13B-alpha, but its receptor tuning, muscle
targets and state-dependent physiology still need evidence. Muscle-force and
activation parameters remain unknown; this is not permission to choose gains
until the leg behaves as desired.

## Reproduction and welfare boundary

Run `.venv/Scripts/python.exe scripts/resolve_motor_targets.py`. Downloads are
cached and source hashes recorded. Outputs:

- `results/motor_targets/consistent_motor_assignments.json`
- `results/motor_targets/malecns_motor_targets.json` (including rejected records)
- `results/motor_targets/fanc_claw_extension_to_motor_pools.json`
- `results/motor_targets/report.json`

The offline suite passes 72 tests, including conflicting target/laterality,
ambiguous IDs and missing-match rejection. No neural state was instantiated,
stimulated or advanced. No welfare assurance is inferred from anatomical matches.
