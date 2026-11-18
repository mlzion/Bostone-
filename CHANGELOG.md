# Changelog

## Plexi v0.4 — continuous audio / real-time workload correction (2026-11-18)

- Replaced full-length interpreted 64-frame partition convolution with a
  nonuniform 64-frame head / 256-frame tail and native complex multiplication.
  Preserved 64-sample global latency, IR timing/gain and all cabinet controls.
- Suspended FFT work after Cabinet bypass settles. Re-enable clears/re-primes
  cabinet histories before fading in; the independent dry delay always advances.
- Added source-derived disjoint memory/page checks, multi-second stream/direct
  FIR regressions, boundary impulses and a native REAPER batch runner with
  load/FFT counters and memory canaries. v0.3 amplifier DSP is unchanged.
- 44 unit tests and 10 REAPER 7.47 Linux render cases pass. Native amp bypass
  matches v0.3 exactly; FIR output matches within a 24-bit half-LSB. No repeated
  loading or buffer-canary corruption occurred in those runs.
- Found a demonstrated real-time budget risk, not a proven indexing defect:
  near-capacity old rendering exceeded audio duration, while new rendering is
  substantially faster. Windows live blips were not reproduced in offline Linux;
  real-time Windows, device CPU/xruns and listening confirmation remain pending.


## Bostone Plexi v0.4 — integrated cabinet IR (2026-11-18)

- Added separate `Bostone_Plexi_v0.4.jsfx`, preserving the v0.3 amp's original
  functions, initialization, controls/defaults and sample-processing code.
- Added bounded mono/stereo WAV loading, native requested-rate decoding/SRC,
  explicit raw/fixed attenuation/linked peak modes, IR level, wet/dry, wet-only
  HP/LP, user-selected tail crop, saved filename and cabinet bypass.
- Added original 64-frame partitioned FFT overlap-add with fixed 64-sample
  latency/PDC and aligned bypass. IR timing and raw gain are retained; no
  default peak normalization, onset shift, silent truncation or limiter.
- Added native Data/BostoneIR selector and text status/reload area. Synchronous
  replacements queue until stopped/faded; missing/invalid/oversized IRs fail
  safely to aligned amp-only output. Capacity is 32768 processed IR frames.
- Added synthetic fixture/numerical/source tests, usage instructions, researched
  ReaVerb mappings, and explicit decoder/filter/SRC/runtime matching limits.
- No v0.3 changes, cabinet assets, waveform display, custom skin, hum removal,
  extra amplifier modeling or automatic merge. REAPER runtime/listening/CPU
  and exact ReaVerb parity remain pending.

## Bostone Plexi v0.3 — standalone amp prototype (2026-11-17)

- Added separately installable `Bostone_Plexi_v0.3.jsfx`, displayed as
  `Bostone Plexi v0.3`; existing Bostone source and version branches are untouched.
- Added bright/coupling frequency shaping, two different biased preamp curves,
  interactive passive RC Bass/Middle/Treble, unequal PI soft saturation, a
  differential bounded-current power stage, and modest per-channel rail memory.
- Added pre-distortion Bass Tightness, Presence HF-feedback surrogate, DC
  removal, bounded wet output, smooth controls/bypass and warm bypass histories.
- Uses actual processing srate throughout; relies on REAPER FX oversampling,
  with no custom resampler, cabinet, IR assets, widening or time effects.
- Reviewed requested references before implementation; recorded selected circuit
  values, variants and explicit behavioral substitutions without exact-model claims.
- Added original numerical/AC tests and installation, settings, research,
  oversampling and matched-loudness Flextron/ReaVerb comparison documentation.
- REAPER parsing, actual 2x/4x host behavior, listening and CPU validation remain
  pending. No listening or amp-equivalence claim is made; PR stays unmerged.

## v0.2 — extended filtering and optional drive (2026-11-17)

- Added separate `Bostone_Preamp_v0.2.jsfx` / `Bostone Preamp v0.2` identity;
  kept v0.1 file byte-for-byte unchanged for side-by-side installation.
- Retained original slider indices/defaults; extended v0.2 High Cut minimum
  and DSP clamp to 400 Hz. Documented actual v0.1 response, cutoff/slopes,
  reference-setting responses, and below/near-bell stability tests.
- Added optional constant-peak band-pass pre-EQ with center, Q, and independent
  level. Original HP+bell+LP remains default; band-pass is an alternative path.
- Added optional cascaded soft clipping, interstage low-pass, partially
  compensated stage gain and trim. Legacy tanh remains default and is
  sample-identical in the independent numerical reference under old settings.
- Added response, legacy equivalence, stereo/isolation, finite automation,
  mode/control ramp, low-cutoff impulse, band-pass bandwidth/level, and
  drive harmonic comparison tests. Static compatibility lint covers both files.
- Updated exact install/update steps, matched-loudness v0.1/v0.2 and Flextron
  A/B protocol, sustained-note decay checks, and provenance documentation.
- Deferred compressor/sustainer to a separate PR after filter/drive validation;
  no oversampling, cabinet assets, external plugin dependency, or VST3 work.
- REAPER runtime compilation/listening/CPU checks remain pending. Offline
  checks are not host validation; no audible amp-equivalence claim is made.

## v0.1 — JSFX syntax corrections (2026-11-17)

- Replaced every scientific-notation guard literal in the production JSFX with
  its equivalent decimal literal: `1e12` becomes `1000000000000`, and `1e-30`
  becomes `0.000000000000000000000000000001`. This addresses the parser errors
  reported around the left/right filter functions in `@init` and the input
  guards in `@sample` on REAPER 7.47 / Windows 11.
- Reviewed all existing executable sections (`@init`, `@slider`, `@sample`).
  There is no `@block` section in v0.1. No caret operators were present; powers
  in future changes must use `pow()`. No further syntax changes were identified
  by this source review; unspecified manual edits cannot be reconstructed.
- Preserved the DSP equations, numeric thresholds, slider ranges/defaults,
  smoothing, bypass behavior, and stereo state separation.
- Added source compatibility lint and regression fixtures for scientific
  literals in all four processing sections, prohibited caret operators,
  unbalanced delimiters, and case-insensitive local/instance name collisions.
  This is a conservative static check, not a complete EEL2 parser.

### Runtime validation status

The user reports that a manually corrected local prototype successfully loads,
responds to all sliders/bypasses, and processes audio in REAPER 7.47 on Windows 11.
That local file was not supplied, so this report does not validate the exact
revision committed here. REAPER is unavailable in the development workspace;
this revision still requires REAPER compilation and audio testing before PR #1
is merged. Passing offline numerical or compatibility checks is insufficient.
