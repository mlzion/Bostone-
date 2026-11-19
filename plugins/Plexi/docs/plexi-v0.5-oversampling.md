# Plexi v0.5 — amplifier oversampling

## Scope and installation

Copy `plugins/Plexi/jsfx/Bostone_Plexi_v0.5.jsfx` into the REAPER resource path's
`Effects/Bostone/` folder and refresh **FX → Scan for new plugins**. Select
**JS: Bostone Plexi v0.5**. Retain v0.3/v0.4 installations and filenames for A/B.
The original 19 amp/cabinet controls and defaults are unchanged. Slider 20 adds
**Amplifier Oversampling: Off (1x), 2x, 4x**, default **Off**. No imported JSFX,
IR, recording, new voicing, compressor, gate, or noise source is added.

The user-confirmed v0.4 cabinet engine remains at the **host FX sample rate**:
same convolution functions, loading/persistence, wet/dry, filters, modes, 64-frame
partitions, 4096-processed-frame cap, IR replacement policy and Data/BostoneIR
location. Internal oversampling does not consume additional cabinet taps.
Externally oversampling the entire FX in REAPER still changes its host FX rate;
avoid stacking it with internal oversampling unless deliberately testing CPU.

## Rate-island decision

All nonlinearities need consideration: biased first triode, rational second
preamp stage, two phase-inverter branches, power-pair current curves, and final
safety saturation. Distortion generated early passes through later filters and
nonlinearities. Independent little rate converters around each waveshaper would
add multiple phase/delay boundaries and require validating each reconstructed
interstage signal. Instead v0.5 runs the **complete contiguous amplifier** at
1x/2x/4x, retaining every equation and interstage order. Cabinet, control smoothing,
bypass ramps and GUI remain at host rate. This costs more than oversampling a
single transfer function, but keeps coupling and dynamic interactions coherent.

All amp poles, tone-stack capacitor companion conductances and sag attack/release
coefficients use `amp_rate = srate * pow(2, mode)`. Tone-control inversion still
updates at the original host cadence (every 16 frames only when changed), not
four times as often. Gains/EQ/Presence/power curves and defaults are not retuned.
The original host-rate `pole()` remains for cabinet filters. `srate` is never
assigned. REAPER reinitializes histories and coefficients on rate changes.

## Original FIR resamplers

Each factor of two uses a symmetric, linear-phase, 65-tap half-band FIR:

```
h[n] = sinc_halfband(n-32) * (0.42 - 0.5*cos(2*pi*n/64) + 0.08*cos(4*pi*n/64))
sinc_halfband(d) = sin(pi*d/2)/(pi*d), with center 0.5
h is normalized to unit DC sum
```

All even-indexed noncentral taps are mathematically zero. Coefficients are
independently calculated decimal literals; no third-party filter source or
coefficient table is imported. This is established windowed-sinc/Blackman FIR
mathematics, not new historical amplifier component research. JSFX functions and
namespaced state follow the [official language reference](https://www.reaper.fm/sdk/js/js.php).

Interpolation is a polyphase evaluation of zero insertion, reconstruction filter
and factor-two gain. It is not sample repetition. The even phase is a delayed
scaled sample; the odd phase uses 16 symmetric pairs. Decimation filters the
complete high-rate history before keeping the even phase. The unused output
phase updates history without calculating a discarded FIR output. Unit tests
compare the polyphase expressions to literal zero-stuff/filter processing.
4x cascades two such 2x stages around the amp.

At normalized high-rate frequency 0.2 the FIR magnitude error is below 0.001;
at 0.3 its magnitude is below 0.0002. These are finite-band checks, not a claim
of infinite alias rejection. The transition region near host Nyquist necessarily
attenuates very high frequencies. Oversampling reduces aliases but does not
make nonlinear processing alias-free.

FIR histories occupy reserved slots 4096–4615, coefficients 2048–2112, dry
alignment 4700–4795 and wet pads 4800–4895, disjoint from amplifier and cabinet
regions. Each channel has separate amplifier, interpolator, decimator and delay
states. No FFT or file loading is added to the oversampling path.

## Latency and switching

The 2x FIR round trip delays 32 host frames; cascaded 4x delays 48. Off gets a
48-frame pad and 2x a 16-frame pad. The dry amp-bypass path is delayed 48 in every
mode. **Total plugin PDC is fixed at 112 frames** (48 amplifier alignment + the
unchanged 64-frame cabinet engine), even with cabinet and/or amp bypassed:

| Rate | Total algorithmic latency |
| --- | --- |
| 44.1 kHz | 2.540 ms |
| 48 kHz | 2.333 ms |
| 96 kHz | 1.167 ms |

This is additional to device/driver latency. Reaper batch compensation is checked
against the old plugin; whole-FX bypass/live routing still needs Windows checks.
The cabinet status's “64-sample engine latency” refers to the cabinet alone.

Changing mode fades the amp contribution to aligned dry over 10 ms, resets only
amp/FIR/wet-pad histories and rate coefficients, primes 256 host frames, then
fades back over 10 ms. The dry ring and cabinet histories keep advancing; no IR
reload, cabinet reset or PDC change occurs. Rapid requests settle on the current
requested mode. A brief dry coloration is expected during the transition; this
is not seamless simultaneous dual-amp morphing. Prefer changing modes while
stopped for tone comparisons. Original Amp Enable keeps the amp warm in bypass.

## Tone and level tradeoffs

Off is the character-preserving default and matches v0.4 exactly after latency
compensation in the recorded sweeps and native stream comparisons. Higher-rate
amp filtering follows the same frequency/time equations, but discrete one-pole
responses and tone-stack frequency warping change with rate. Reduced aliases
also change harmonic balance. This is not a promise that 2x/4x null against 1x.

The measurement report quantifies these differences. At tiny input, 4x versus
1x differs by roughly +0.06 to +0.21 dB around 200–1000 Hz and up to about
-1.48 dB near 10 kHz at 44.1 kHz. Differences shrink at 96 kHz. There is no
intentional EQ/gain compensation to disguise the rate-dependent result. The user
must assess these differences by listening before choosing a preferred mode.

The original safety waveshaper remains before the decimator, so FIR ringing can
exceed its instantaneous high-rate sample ceiling. The FIR L1 norm is about
1.683; conservative wet-only bounds before cabinet are 0.8*output_gain times
1, 1.683 or 1.683 squared for 1x/2x/4x. These are worst mathematical bounds,
not typical levels or an added limiter. Keep normal monitoring headroom. Cabinet
IR gain/normalization may increase levels as in v0.4; no extra compensation is
introduced. Default sweep peaks are reported separately.

## Performance and limits

Stereo amp calls per host frame are 2/4/8. Resampling uses fixed FIR work per
frame; no nonuniform FFT scheduler, periodic long-tail job, dynamic allocation
or periodic IR reload is introduced. The cabinet's bounded 64-frame workload
and capacity are unchanged. At 2x/4x each channel uses respectively 34/102
symmetric FIR coefficient products per host frame, plus simple history updates.
Off does not execute resampling FIRs. Mode resets are bounded small clears and
a single tone-network rebuild behind the dry fade.

Batch throughput and 64-frame elapsed wall-time probes are not audio-device CPU
percentages. The latter include process descheduling and can exceed device
budgets on a shared Linux host; no worst-case real-time certification is claimed.
Windows RT CPU, callback peaks and underruns must be measured at the user's
actual buffer size. 4x at 96 kHz is expensive; use Off/2x if its added rejection
is not useful or headroom is insufficient. Do not trade reliable playback for a
higher mode label. No auto-switching, hidden limiter or additional feature is
added. See [measurements](plexi-v0.5-measurements.md) and
[Windows listening checklist](plexi-v0.5-testing.md).
