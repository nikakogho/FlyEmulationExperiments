# Unsent technical query

Subject: Reproducing Figure 5c from Luo_Huang_2024_MB_model

I am reproducing the recurrent model from Huang, Luo et al. (Nature 2024), using
repository commit 5d7c08a9a88f923169a0c3008aca68af421e9a7f without parameter refitting.

A Python translation matches all 144 values saved in the repository's native
MATLAB three-module attractive/repulsive fitting figures to 1e-10 Hz, using the
fitting script's protocol. With the Figure 5c example's protocol and all 10,000
deposited samples, however, the medians differ from the published source workbook
by up to 0.44 Hz (RMSE 0.1846 Hz across 48 values).

The released solver uses an alpha2 MBON evoked-rate ceiling of 8.9 Hz, whereas
the source workbook plateaus at 8.46 Hz. Changing that ceiling alone, or using
the alternate 17-Apr-2024 parameter samples, does not resolve the discrepancies.

Could you identify the exact code revision, constants and parameter-sample
archive used to generate 41586_2024_7819_MOESM10_ESM.xlsx, Panel c?

For a later online implementation, could you also clarify whether Appendix
Eq. 5.8 should describe decay of weight deviations from the initial weight,
as in the released code, and whether any specific kernel constants from
Eqs. 3.2–3.3 were used beyond the two fitted fixed-delay amplitudes?

The present implementation, source-cell comparisons and numerical checks are
available to share if useful.
