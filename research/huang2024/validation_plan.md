# Reproduction gate, set before executing the Python model

Source: Huang, Luo et al., Nature 2024, DOI 10.1038/s41586-024-07819-w.
Author code: schnitzer-lab/Luo_Huang_2024_MB_model at
5d7c08a9a88f923169a0c3008aca68af421e9a7f (GPL-3.0-or-later).

1. Preserve author files and fitted parameter samples. Do not refit.
2. Port the released recurrent algorithm and Figure 5c schedule literally.
3. Test parameter placement against Table 3, protocol timestamps, signed local
   updates, frozen-weight control, odor permutation, bounded MBON rates,
   decay across the 3-hour boundary and numerical agreement with an independent
   direct solution of the neural graph. Numerical tolerance: 1e-10 absolute Hz.
4. Compute all 10,000 supplied parameter samples. Compare medians with the
   author-published modeling values for all 48 Figure 5c cells (6 neuron types,
   2 odors, 4 time points). Separate model reproduction from fit to experimental
   animals. Require every cell within 0.05 Hz, a pre-execution engineering
   reproduction tolerance, not a biological significance threshold.
5. Do not retune parameters or relax this gate after seeing output. Investigate
   discrepancies as code/data/version/protocol issues. Record exceptions openly.
6. A failure blocks promotion to the spiking circuit and garden. Passing software
   tests alone does not establish biological accuracy. A successful reproduction
   would still need separately specified temporal and spiking validation.

Known source distinctions to audit: appendix Eq. 5.8 decays total weight toward
zero, whereas released code decays learned deviations toward initial weight;
code applies recovery even during odor and normalizes updates by duration/90 s.
Retain these code behaviors in this reproduction. General timing constants cannot
be recovered uniquely from the two fitted fixed-delay coefficients.
