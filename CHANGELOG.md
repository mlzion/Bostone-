# Changelog

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
