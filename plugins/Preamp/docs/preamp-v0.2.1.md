# Bostone Preamp v0.2.1 — expanded pre-EQ range

v0.2.1 is a separate installation for stronger bass removal and higher mid-bell
placement before Plexi. It copies v0.2 processing exactly except for the display
name and these three slider ranges and matching DSP target clamps:

| Index | Control | v0.2 | v0.2.1 | Default (unchanged) |
| --- | --- | --- | --- | --- |
| 2 | Pre Low Cut | 40–300 Hz | 40–1000 Hz | 80 Hz |
| 4 | Pre Low-Mid Frequency | 150–1000 Hz | 150–2000 Hz | 400 Hz |
| 5 | Pre High Cut | 400–15000 Hz | 400–10000 Hz | 10000 Hz |

No slider is added, removed or reordered. All 25 defaults remain valid and
unchanged. The Low-Mid gain remains ±12 dB. Original HP/LP slopes remain second
order (12 dB/octave asymptotically, Q=1/sqrt(2)), bell Q remains 1, and cutoffs
remain -3.0103 dB points of the isolated HP/LP, not brick-wall edges. The existing
0.45*srate frequency safeguard also remains. No coefficient formula changes.

Band-pass mode, its center/Q/level ranges, cascaded/legacy drive, post-EQ,
gain staging, stereo state separation, 20 ms parameter smoothing and 10 ms
bypass/mode ramps are unchanged. **Low Cut, Low-Mid and High Cut affect Legacy
HP/Bell/LP pre-EQ only**; select Pre-EQ Mode = Legacy and Pre-EQ Enable = On to
audition the new ranges. In Band-pass mode the alternative pre-EQ still replaces
that chain, so changing these inactive controls will not affect audio.

## Installation and update (REAPER 7.x / Windows 11)

1. Use **Options → Show REAPER resource path in explorer/finder** and open/create
   `Effects/Bostone`. A typical standard installation is
   `%APPDATA%\REAPER\Effects\Bostone`.
2. Copy `plugins/Preamp/jsfx/Bostone_Preamp_v0.2.1.jsfx` there, retaining the exact filename.
   Do not overwrite/rename `Bostone_Preamp.jsfx`, `Bostone_Preamp_v0.2.jsfx`, or
   `Bostone_Plexi_v0.3.jsfx`. No imports or other runtime files are needed.
3. Refresh using **FX → Scan for new plugins** in the FX browser. Search for
   **JS: Bostone Preamp v0.2.1**, distinct from **Bostone Preamp v0.2**,
   **Bostone v0.1 - Preamp Prototype**, and **Bostone Plexi v0.3**.
   Reopen the browser/restart REAPER if needed; check for a hidden `.txt` suffix.
4. Add the new FX to a temporary test project and open **Edit** to verify it
   compiles. Existing projects continue using their original plugin identities.
5. To compare, transfer original values manually and activate only one preamp at
   a time. Shared-range values should match v0.2 after states/smoothing settle.
   Old High Cut settings above 10000 Hz cannot be reproduced in v0.2.1; keep
   v0.2 available for those settings. There is no automatic preset migration.
   Avoid transferring normalized automation blindly across changed ranges.

For a first test, keep default gains, set Pre-EQ Mode to Legacy, and compare
Low Cut 80/300/800/1000 Hz ahead of Plexi. 800 Hz is an aggressive reduction of
low fundamentals, not a claim of exact Boston tone. Try Low-Mid Frequency
1000/1500/2000 Hz with a moderate nonzero gain, and High Cut 400/2000/10000 Hz.
Keep levels modest and compare at matched perceived loudness. Suggested chain:
**v0.2.1 → Plexi v0.3 → ReaVerb (your cabinet IR)**. No IR is bundled or changed.

## Automated validation

Run the complete repository suite:

```console
python3 run_tests.py --plugin Preamp
```

The new tests:

- Verify new production source is exactly v0.2 with only the identity plus six
  range/clamp edits, keeping all processing expressions unchanged.
- Check byte identity of v0.1, v0.2 and Plexi against their existing versions,
  unique displayed FX names, unchanged defaults, and all-source syntax lint.
- Check both endpoints and out-of-range clamps reach the expected filter targets
  at 44.1/48 kHz, including HP 800 Hz; isolated HP/LP cutoff response and bell
  center gain agree with the expected mathematics.
- Measure more than 30 dB additional 100 Hz attenuation at HP 1000 versus 40 Hz
  in the independent model; verify the higher bell and reduced LP limit change
  their responses instead of being silently clamped to old values.
- Check poles, impulse decay with crossed/nearby cutoffs, finite extreme
  automation, channel isolation, silence, exact settled master bypass and
  bounded sample changes during endpoint automation.
- Compare v0.2/v0.2.1 numerical output exactly under shared settings in all
  pre-EQ/drive mode combinations, including automation and bypass.

The numerical harness does not compile or execute the JSFX source. Source lint
is conservative and cannot prove EEL2 validity. This version introduces no new
functions, pow() calls or caret operators: original exp/log math is retained.
The existing JSFX compatibility check scans the new file alongside older files.

## Manual REAPER acceptance — pending

REAPER is unavailable in the development workspace. Compilation, listening,
click audibility, host automation integration and actual DSP behavior in REAPER
remain pending. No offline result is a guarantee of successful host compilation
or completely click-free audio.

1. Confirm distinct installation/identity, 25 sliders, default values and all
   three new endpoint ranges in the JSFX editor. Record REAPER build and rate.
2. In Legacy pre-EQ, use a low-level generated sine/sweep with distortion and
   post-EQ disabled. Compare HP 300/800/1000 Hz at 100/800/1000 Hz, bell center
   1000/2000 Hz with gain +6 dB, and LP 400/10000 Hz. Allow at least 150 ms for
   smoother settling. Verify knobs actually change meters/spectrum/audio.
3. Repeat at 44.1/48 kHz, including HP 1000 + bell 2000 + LP 400 extremes.
   Test silence, impulse tails and left-only/right-only input for instability,
   crosstalk, non-finite meters, DC shifts or unexpected output bursts.
4. Automate the three changed controls and all enables; listen for clicks and
   transient problems. Check Band-pass and Cascaded modes still behave as v0.2.
   Confirm unchanged dry master bypass after the 10 ms ramp.
5. Compare v0.2/v0.2.1 at identical shared settings, then new HP 800 before Plexi,
   at matched perceived loudness. Save/reopen projects and presets; confirm
   old preamps and the separate Plexi retain their independent settings.

Do not merge automatically; review the PR and record host acceptance results.

### Recorded offline result — 2026-11-18

The full suite passed **38 tests** (32 existing regressions plus six v0.2.1
cases) in Linux/Python. Source compatibility lint checked all four JSFX files.
Whitespace checks passed. These results do not include REAPER runtime audio.
