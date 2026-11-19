# Baseline filters and v0.2 alternatives

## Actual v0.1 response

The pre-EQ is a cascade of RBJ second-order HP (Q = 1/sqrt(2)), bell (Q = 1),
and second-order LP (Q = 1/sqrt(2)). HP and LP each have asymptotic 12 dB/octave
slopes in the analog prototype, with bilinear frequency warping in digital form.
They are not notches or brick walls. At each filter's named cutoff its isolated
response is -3.0103 dB, not zero attenuation or a passband edge. Attenuation
changes gradually on either side, and the cascade/bell further alters the total
level at that frequency. Near Nyquist the slope in ordinary Hz is steeper due
to warping; a fixed 12 dB/octave number there would be misleading.

Original v0.1 ranges remain: HP 40–300 Hz (80 default), bell 150–1000 Hz
(400 default), bell gain ±12 dB (0 default), LP 2000–15000 Hz (10000 default).
v0.2 changes only the LP lower endpoint to 400 Hz. The DSP target clamp changes
with the slider declaration. All other original indices, defaults, and ranges
remain. Actual frequency remains bounded by 0.45 × sample rate.

The issue's reference settings are HP 218 Hz, bell +6.4 dB at 685 Hz, LP 2000 Hz.
Calculated **combined pre-EQ** gain (not including distortion or post-EQ):

| Sample rate | At 218 Hz | At 400 Hz | At 685 Hz | At 2000 Hz |
| --- | --- | --- | --- | --- |
| 44100 Hz | -2.255 dB | +2.454 dB | +6.298 dB | -2.137 dB |
| 48000 Hz | -2.254 dB | +2.455 dB | +6.298 dB | -2.135 dB |
| 96000 Hz | -2.254 dB | +2.456 dB | +6.297 dB | -2.128 dB |

These settings are useful for comparison, not an exact single band-pass design.
Frequency-response tests evaluate the transfer functions at 44.1/48/96 kHz,
including isolated -3 dB cutoffs, prototype slopes on warped frequency, and
combined reference response. Impulse tests cover LP 400 Hz below/at/above bell
centers 150, 400, 685, and 1000 Hz with +12 dB boost.

## Optional band-pass

Constant-peak RBJ band-pass: alpha = sin(w)/(2Q); numerator = [alpha, 0, -alpha],
denominator = [1+alpha, -2cos(w), 1-alpha], then normalize by 1+alpha.
It attenuates frequencies outside its band, approaches zero at DC and Nyquist,
and has unity center gain before the separate Level control. Q changes bandwidth,
not the center gain. At low frequency its -3 dB bandwidth is approximately f0/Q;
use Q rather than an exact linear-Hz bandwidth label because of digital warping.

For exact -3 dB edges: let t0 = tan(pi*f0/Fs), then
`t± = t0 * (sqrt(1 + 1/(4*Q*Q)) ± 1/(2*Q))`,
`f± = Fs/pi * atan(t±)`. The center is symmetric in warped frequency, not
necessarily halfway between edges in Hz. Tests cover centers 150/685/4000 Hz
and Q 0.25/1/4 at all three primary rates, including pole stability.

The band-pass and original pre-EQ run in parallel from the input-gain output.
The mode selector crossfades their outputs; it does not stack them. Pre-EQ
Enable bypasses the selected output. This makes the single band-pass experiment
explicitly different from the user's HP+bell+LP reference.
