# DSP implementation notes

## Filters

The six normalized biquads use the RBJ Audio EQ Cookbook equations, independently
written for this project. Each filter implements direct form I:

`y[n] = b0*x[n] + b1*x[n-1] + b2*x[n-2] - a1*y[n-1] - a2*y[n-2]`.

All coefficients are divided by a0. Separate left/right x and y histories live
in JSFX function-instance namespaces. Direct form I keeps histories in signal
units while coefficients change. No third-party DSP source is included.
See [fixed Q and shelf slope choices](signal-chain.md).

Frequency is clamped to `[10 Hz, 0.45 × sample rate]` after clamping the user
control to its advertised range. Thus the full 15 kHz high-cut setting is
available at 44.1 kHz and above; low sample rates reduce the actual cutoff.
The smoothing constants and filter targets use REAPER's current `srate`.
Normal JSFX reinitialization is retained: there is no `ext_noinit` override.

## Smoothing and bypass

Gain multipliers, drive, and normalized filter coefficients use a sample-by-sample
one-pole smoother: `value += alpha*(target-value)`, where
`alpha = 1-exp(-1/(0.020*srate))`. This is a 20 ms time constant, approximately
60 ms to travel 95% of a step. Expensive trigonometric calculations occur in
`@slider`, not per sample. Coefficients snap to their initial targets on load.

Coefficient interpolation makes the path of normalized second-order denominators
stay inside the convex frozen-coefficient stability region. This does not prove
arbitrary time-varying filter stability or eliminate every audible transient;
rapid automation still needs host testing. The offline stress tests cover the
specified parameter bounds at seven sample rates. Parameter smoothing applies
to coefficients rather than producing a prescribed Hz/dB interpolation curve.

Bypass mix values use linear 10 ms ramps. Reversing a switch mid-ramp reverses
from its current position. Endpoints are exact. The wet path continues running
so re-enabling a filter does not resume an old stored tail. This also means
master bypass does not save processing CPU.

## Gain staging and soft clipping

Drive is a direct amplitude multiplier, without automatic makeup. For low
signals the distortion gain is approximately Drive. At higher amplitudes tanh
compresses smoothly toward ±1. The default drive of 3 is about +9.54 dB in the
small-signal region; the output stage defaults to -6 dB. This is a starting
point for listening, not loudness matching. Input and output gains are linear
amplitude multipliers derived from dB.

For portability, a local JSFX function implements mathematical tanh:
`sign(x)*(1-exp(-2*abs(x)))/(1+exp(-2*abs(x)))`.
The exponential argument is never positive, avoiding exponential overflow.
Drive 1 remains nonlinear. Distortion Enable Off provides a linear path.

Post-EQ boosts can exceed the distortion's ±1 bound. No hard output clip or
limiter is added; monitor conservatively and level-match comparisons. The
original guitar pickup, playing, later cabinet shaping, and monitoring system
will materially affect perceived tone. This is not a circuit emulation.

## Numeric containment

UI targets are range-clamped, with NaN targets replaced by their lower bound.
Host input that is NaN, infinite, or above 1e12 in absolute value is replaced
with zero. If a biquad output is NaN or above 1e12, that filter channel's
histories reset and that output sample becomes zero. Very small filter outputs
below 1e-30 become zero to suppress denormal tails. These are fault guards,
not audio limiters. Fault recovery may be audible. Ordinary finite master
bypass is unchanged; sanitization still applies to pathological input.

## Aliasing, CPU, and validation limits

Tanh generates harmonics above Nyquist, which fold into the audio band in this
non-oversampled prototype. The pre low-pass reduces input bandwidth but cannot
eliminate nonlinear aliasing. Plan to evaluate oversampling after the voicing
is settled. No third-party resampling implementation is included.

Six stereo biquads, coefficient smoothing, and two bounded exponentials per
sample are intended to be modest work; no allocations occur in `@sample`.
Actual CPU cost has not been measured in REAPER. The Python harness verifies
DSP mathematics only. REAPER EEL2 compilation, lifecycle behavior, and audible
clicks remain manual validation requirements before release acceptance.

## v0.2 implementation

`Bostone_Preamp_v0.2.jsfx` copies the corrected v0.1 math without editing the
original file. Its 17 original sliders keep indices and defaults; only slider5's
minimum and corresponding clamp change from 2000 to 400 Hz. New controls append
at 18–25. The new band-pass math and frequency-response details are documented in
[filter-response.md](filter-response.md). All new amplitude/coefficients use the
same 20 ms smoother; mode selectors use 10 ms ramps. A zero mode mix explicitly
selects the legacy path without an extra blend. New filter states are independent
per channel, initialized on load, and retain the same fault/denormal containment.

### Cascaded drive experiment

Let d = existing Drive, g = 10^(StageGainDB/20), and t = 10^(TrimDB/20):

`first = tanh(d*x)`

`second = tanh(g*LP(first)) * t / sqrt(g)`

The interstage LP is a second-order RBJ low-pass (Q = 1/sqrt(2)), adjustable
800–12000 Hz and sample-rate-clamped. Stage Gain is 0–18 dB. Division by sqrt(g)
is deliberately partial compensation: small-signal second-stage gain is sqrt(g),
and the saturated peak bound is t/sqrt(g). Trim (±12 dB, default 0) allows
level matching; this is not automatic perceptual loudness matching. Even at 0 dB
stage gain a second tanh and the LP remain in this mode. Use Legacy for exactly
the original transfer. Output gain still defaults to -6 dB, with no final limiter.

Numerical example: 500 Hz sine at 0.1 amplitude, Drive 10, Stage Gain 12 dB,
Interstage Cut 6000 Hz, Trim 0 dB, EQ and gain stages bypassed at 48 kHz:
legacy third/fundamental ratio ≈0.06683, cascaded ≈0.26776. RMS decreases from
≈0.57523 to ≈0.45436 due to compensation and filtering. This measures a different
nonlinear response with a retained fundamental; it does not establish audible
note definition or amp equivalence. Listening tests at matched loudness are pending.

The interstage LP reduces high-frequency energy entering the second nonlinear
stage. It does not remove aliases already generated by the first stage or prevent
aliases from the second. Oversampling is deferred; neither model nor production
claims alias-free processing. v0.2 runs eight stereo biquads and four tanh
identities per frame; CPU cost remains unmeasured in REAPER.

### Sustain deferral and compatibility

The issue explicitly allows deferring the compressor/sustainer. It is deferred
to a separate PR after filter/drive runtime tests and listening feedback. There
is no envelope detector, makeup, gate, or noise-floor amplification from a new
compressor in this change. New drive gain can still raise noise and change decay.
This version is not a JUCE/VST3 implementation or circuit emulation.

The new source uses the same EEL2 function/instance/local/conditional syntax as
the corrected v0.1 file, with decimal literals and no caret or pow() calls.
There is no @block section; coefficient targets are prepared in @slider and
sample processing occurs in @sample. Static lint checks both JSFX files, but
REAPER parsing, host automation, save/reload behavior, CPU, and listening quality
are pending because REAPER is unavailable in this workspace.
