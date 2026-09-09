# Step 4: sensory route and learning-compartment validation

**Result: step 4 did not pass; step 5 was not run.** The investigation narrowed
the anatomical route and fixed a transport limitation, but did not establish
the required sensory transfer function or fine modulatory assignment.

## Route supported by sources and local graph

A tractable candidate is photoreceptors → aMe12 → KCg-d → MBON01, with
PAM01 modulation of the gamma5 branch. This avoids assuming that motion
detectors connect directly to visual Kenyon cells.

The aMe12 literature describes connections with pale photoreceptor columns and
projections to visual Kenyon cells. This supports a candidate spectral route,
not a complete measured input-output function for our seven annotated aMe12
neurons. [Kind et al., photoreceptor-target study](https://elifesciences.org/articles/71858).
Experimental work separately supports visual KCs and distinguishes pathways
needed for color and brightness learning; it does not identify a calibrated
transfer function for every cell in our reconstruction.
[Vogt et al., 2016](https://elifesciences.org/articles/14009).

The unthresholded local connection table contains:

| Anatomical connection | Synapse count |
|---|---:|
| R7/R8 → aMe12 | 933 |
| aMe12 → visual KCg-d | 2,511, reaching 168 KCs |
| KCg-d → MBON01 | 630 across 221 aggregated edges |
| PAM01 → MBON01 | 306 |

Exact root IDs and connection counts are exported as CSVs in `results/step4/`.
These establish anatomical edges, not their functional response amplitudes,
time constants or the strengths of dopamine-induced plasticity.

MBON01 spans gamma5 and beta-prime2a; gamma KC input supports a coarse gamma5
assignment. [MBON01 anatomy and plasticity experiment](https://www.eneuro.org/content/10/10/ENEURO.0275-23.2023).
However, PAM01 includes anatomically distinct subdivisions. The connectome
study explicitly describes feedback DANs restricted within gamma5 and different
MBON targeting. Assigning all PAM01 neurons uniformly to every gamma5 synapse
would discard this distinction.
[Mushroom-body connectome study](https://elifesciences.org/articles/62576).

Thus the coarse compartment hypothesis is supported, while a fine per-synapse
modulator mapping is not validated. The supplied table aggregates synapses
without their compartment positions. Additional type/anatomical information
may resolve some assignments; this is not a claim that every assignment
necessarily requires new experiments.

## Concrete information-loss test and fix

The current grayscale motion front end makes our green and blue cue colors
identical: their channel averages are equal. The maximum difference across
all 721 receptors and both eyes is exactly zero. Swapping G/B channels in an
actual saved scene also leaves the encoded input exactly unchanged. A model
receiving those identical inputs cannot recover their color identity from
that input alone. This does not imply that biological flies cannot distinguish
the cues, or that different visual features such as brightness could not work.

Added `RetinalBridge.encode_rgb`, which retains a separate R/G/B average at
each receptor while preserving the checked ordering and excluding background
pixels. The two test cues now differ by 0.9490 in their normalized channel
values. The existing grayscale method remains available for FlyVis motion
tests; no unsupported three-channel input was forced into that model.

This is a necessary transport fix, not calibrated spectral physiology. RGB
display channels are not R7/R8 responses, lack a specified emission spectrum,
and cannot reconstruct UV from ordinary rendered RGB. The local cell labels
used here identify R7/R8, not a validated per-receptor retinal mosaic and
spectral calibration for this bridge. Nor do anatomical counts alone provide
the aMe12 response dynamics.

## Tests and decision

All **43 base-environment unit tests pass**, including a regression test that
demonstrates grayscale aliasing and preservation in the separate RGB output.
`scripts/validate_step4.py` runs the actual-retina/recorded-scene checks and
exports the candidate anatomical edges. Its diagnostics pass, but its
integration gate intentionally returns exit code 1.

```powershell
.venv/Scripts/python.exe -m unittest discover -s tests -v
.venv/Scripts/python.exe scripts/validate_step4.py
```

Evidence: `results/step4/checks.json`, the connection CSVs in that directory,
`results/step4.log`, and `results/step4_unit_tests.log`. The validation script
refreshes its own fixed output directory; prior experimental cohorts are
unchanged. No body, whole-brain or new visual-network simulation ran in this
stage; the work used anatomy, recorded images and arithmetic tests.

The gate still requires a documented sensory transfer function and a justified
modulatory assignment. A hand-written blue-to-aMe12 gain could make an exploratory
model run, but would not make this validation succeed. Step 5 was conditional
on success, so another embodied learning cohort was not launched. Improved
biological learning remains unproven.
