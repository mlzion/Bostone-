# Changelog

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
