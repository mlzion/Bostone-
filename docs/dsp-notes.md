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
