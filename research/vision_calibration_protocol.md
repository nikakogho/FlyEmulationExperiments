# Frozen offline visual calibration protocol

Selected candidate: the published FlyVis connectome-constrained visual model,
checkpoint flow/0000/000 (the upstream default), without retraining. This
contains fitted functional parameters; it is not determined by anatomy alone.
Source: https://github.com/TuragaLab/flyvis and
https://www.nature.com/articles/s41586-024-07939-3 .

Use the upstream MovingEdge generator at 200 Hz, speed 19, offsets [-10,11],
height 80, 1 s pre/post padding, both edge polarities and four cardinal angles.
Measure the central cell of each T4/T5 subtype. Expected preferred angles,
in upstream stimulus coordinates: a=180, b=0, c=90, d=270.

Before inspecting any model responses, define a qualitative gate:
1. All responses finite, and the pretrained parameters unchanged.
2. For each of eight T4/T5 subtypes, the baseline-subtracted positive peak
   response at its expected preferred direction exceeds its opposite direction,
   with (preferred-null)/(preferred+null) >= 0.2. Use ON edges for T4 and OFF
   edges for T5. If the denominator is zero, the gate fails.
3. Each subtype's maximum over cardinal directions is larger for its expected
   polarity (T4 ON, T5 OFF) than for the other polarity.
4. A constant gray control has maximum central-cell change < 0.001 after the
   first second. This is an engineering equilibrium check in model units.

These thresholds are engineering gates, not reported biological confidence
intervals. Retain every failure; do not select another checkpoint to obtain a
pass. Record full central-cell response traces and stimulus metadata. No motor
decoder, goal location, reward input, optimizer, whole-brain model or body is
connected. Synthetic edge movies are isolated visual-system probes, not
aversive behavioral experiments. Passing would establish qualitative model
tuning only, not calibrated real-fly response magnitude, normal perception,
learning, welfare, or an anatomical mapping into our existing LightBrain.

After a pass, temporal convergence at 400 Hz should be checked before integration.
If the gate fails, diagnose the mismatch before any closed-loop use.

Convergence gate (specified before either response set is inspected): the same
qualitative checks must pass at 400 Hz, maximum absolute direction-index change
must be <= 0.05, and expected-direction peak change must be <= 10% relative to
the 400 Hz result for each subtype. Compare equivalent physical time windows.
