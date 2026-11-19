# Validation

## Automated offline checks

From the repository root with Python 3.9+:

```console
python -m unittest discover -s tests -v
```

The harness is an independent numerical model in `plugins/Preamp/tests/offline_dsp.py`, not a
JSFX parser, EEL2 interpreter, or REAPER integration. A lightweight source
contract check detects a few important configuration mismatches but does not
prove source/model equivalence. Keep both implementations aligned when changing
DSP. Passing these checks does not establish that REAPER compiles the file.

Nine automated test cases passed on 2026-11-17 in Linux/Python. They cover:

- Exact silence, channel isolation in both directions, and stereo symmetry.
- Pole radii below one for endpoint frequencies and gains, plus HP/LP endpoints,
  bell center gain, and shelf endpoint gain.
- Input/output gain values, disabled sections, and master dry bypass after ramps.
- Drive transfer against Python's mathematical tanh.
- Finite outputs under extreme controls and seeded automation at 22050, 32000,
  44100, 48000, 88200, 96000, and 192000 Hz, including malformed host input.
- Control changes on a continuous 440 Hz sine at 0.01 amplitude: maximum
  successive-sample change below 0.02 full scale for individually exercised
  controls at 48 kHz. This is a regression bound, not proof of inaudibility.

No REAPER runtime test, Windows installation test, CPU measurement, or listening
test has been performed. Manual checks below are pending.

## Manual REAPER 7.x / Windows 11 acceptance

1. Follow the README installation steps. Add the JSFX to a stereo track. Open
   **Edit** and confirm successful compilation. Record exact REAPER build and
   sample rate. Confirm the 17 controls and defaults match the README.
2. Use a generated sine or your own DI guitar recording; do not commit recordings.
   Start at low monitor volume. Disable all five stages and compare with track
   FX bypass. Output should null after the 10 ms enable ramps settle.
3. Test silence on a new instance, then after playing audio and allowing filter
   tails to decay. Confirm no persistent noise, NaN meters, or self-oscillation.
4. Send only left, then only right; confirm the other output remains silent.
5. With pre-EQ, distortion, and post-EQ disabled, verify input/output gain values
   using a sine and meters. Allow about 150 ms for smoothed changes to settle.
   Test Input and Output Enable separately at nonzero gain settings.
6. Enable pre-EQ: sweep cuts and bell settings; compare each extreme. Disable
   it and confirm the complete pre-EQ is removed. It has three filters sharing
   a single section enable switch.
7. Disable EQs and test Drive 1, 3, 20 on a sine and DI. Verify increasing
   saturation, odd harmonics, and removal using Distortion Enable.
8. Enable post-EQ and sweep each gain; sweep mid frequency with a nonzero mid
   gain. Confirm low shelf at 150 Hz and high shelf at 4 kHz. Check section bypass.
9. Automate every control rapidly, including bypass reversals during ramps.
   Listen for clicks and excessive bursts. Repeat while stopped/restarted,
   across loop boundaries, and when re-enabling bypassed sections after silence.
   Crossfade coloration is expected; report objectionable transients.
10. Turn Master Bypass on with non-neutral settings. After 10 ms, null against
    the original signal. Confirm dry amplitude regardless of output gain.
11. Repeat at 44.1, 48, 88.2, 96, and 192 kHz; change project/device rate while
    stopped. Save/reopen project and preset, duplicate instances, seek, and verify
    state initialization and parameter recall. Also check mono track routing.
12. Compare idle/playback CPU with REAPER's performance meter; record block
    size, CPU, instance count, and sample rate. Render a short passage and
    compare with live playback. Listen for expected aliasing at high drive.

Use a temporary project and conservatively set monitoring volume: this prototype
has no final limiter. A listening verdict is needed before planning the JUCE port.

## Manual result log

| REAPER build / Windows build | Rate / block size | Procedure | Result / notes |
| --- | --- | --- | --- |
| Not yet tested | — | All manual steps | Pending user validation |

## Syntax-correction follow-up (2026-11-17)

The suite now also checks the actual `.jsfx` files for scientific literals,
caret operators, mismatched parentheses/brackets, and case-insensitive variable
collisions. Regression fixtures verify detection in `@init`, `@slider`, `@block`,
and `@sample`; comments and quoted text are ignored. Decimal replacements are
checked for numeric equivalence. This lint is intentionally conservative and
cannot guarantee EEL2 compilation or validate all syntax and function APIs.

The user reports successful REAPER 7.47 / Windows 11 operation after manual
syntax fixes. The manually edited file was not available for comparison. The
repository revision replaces all scientific literals and needs its own host
retest: install this exact PR version, confirm no JSFX editor errors, exercise
all 17 sliders and stage/master bypass switches, and verify stereo audio.
REAPER is not installed in this development workspace, so no runtime validation
of this revision was performed here. Keep PR #1 unmerged until that retest passes.
See [changelog](../../../CHANGELOG.md) for the exact scope of corrections.

After these corrections, all 14 tests passed on 2026-11-17 (the original nine
numerical/source-contract cases plus five compatibility regression cases).

## v0.2 acceptance and A/B plan

### Automated scope

Run the same unittest discovery command above. It now also covers the v0.2
numerical model and actual-source compatibility lint. Tests verify:

- Frozen v0.1 blob identity, separate v0.2 description, all original indices and
  defaults, exact High Cut slider/clamp minimum, and new control defaults.
- Sample-identical legacy model output at 44.1/48/96 kHz for defaults, the issue's
  reference settings, unused new-control changes, original automation/bypasses.
- Isolated -3.0103 dB HP/LP cutoffs and slopes in warped frequency; combined
  reference response; LP 400 Hz impulse decay with bell frequencies 150–1000 Hz.
- Band-pass unity center gain, -3 dB bandwidth, poles, DC/Nyquist rejection,
  independent center-level scaling, and independence from unused HP/bell/LP.
- New paths' silence, stereo isolation, finite output and automation extremes
  at seven sample rates; low-level new-control/selector transition bounds.
- Selected bypass output after ramp settling and a level-independent
  third/fundamental increase in cascaded drive while retaining a fundamental.

The numerical model does not execute the production source. Exact legacy
comparison refers to model output, not a measured REAPER null. Source lint is
not a full EEL2 compiler. Audible note definition, pumping/noise, aliases,
instance recall, sample-rate switching, and CPU remain manual checks.

### Side-by-side installation and update

1. Open REAPER's resource path using Options. In its `Effects/Bostone` directory,
   leave `Bostone_Preamp.jsfx` untouched and copy `Bostone_Preamp_v0.2.jsfx` beside
   it. Typical nonportable Windows location:
   `%APPDATA%\REAPER\Effects\Bostone\Bostone_Preamp_v0.2.jsfx`.
2. Use FX browser **FX → Scan for new plugins**. Confirm two distinct entries:
   **JS: Bostone v0.1 - Preamp Prototype** and **JS: Bostone Preamp v0.2**.
   Check that neither file has a hidden `.txt` suffix or a duplicate elsewhere.
3. In a temporary project insert both on one track. Open each JSFX editor and
   confirm compilation; v0.1 has 17 controls, v0.2 has 25. Keep only one FX
   enabled via REAPER's instance bypass checkbox. Both active would stack them.
   Set different outputs on each; toggle to confirm independent instance state.
4. For v0.2 updates replace only its versioned file and refresh the browser.
   Save instance settings first and remove/reinsert v0.2 in the temporary test
   project to ensure the disk revision is loaded. Existing v0.1 projects and
   preset references must still open normally. Save/reopen and test recall.

### Legacy null and filter exploration

5. Set v0.2 selectors 18 and 22 to Legacy. Match all original 17 values manually
   with v0.1. On duplicate tracks play the same DI, phase-invert one, and allow
   filter tails/smoothing to settle. Confirm a null with both instances enabled
   on separate tracks. Restore normal routing before listening comparisons.
6. Start with the issue's reference: input 0 dB, HP 218 Hz, bell +6.4 dB / 685 Hz,
   LP 2000 Hz, Drive 20, post low -8.2 dB, mid +5.1 dB / 717 Hz, high -12 dB,
   output -2.6 dB. All sections enabled. Do not change the v0.1 track further.
   On v0.2 sweep LP from 2000 down to 400 Hz; listen below/near the bell center.
7. Compare v0.2 Legacy pre-EQ against Band-pass at 685 Hz, Q 1, Level 0 dB.
   Sweep Q 0.25–4 and Level ±12 dB; verify narrower bandwidth does not itself
   boost the center. Original HP/bell/LP controls should have no effect while
   Band-pass is fully selected, and their saved values should return on Legacy.

### Bostone alone vs Bostone + Flextron at matched loudness

8. Use your own identical DI source on two aligned tracks: A = Bostone v0.2
   alone; B = identical Bostone settings followed by the user's Flextron Marshall
   simulation. Obtain/use Flextron separately; it is not bundled or required.
   Disable unrelated FX. Avoid active master dynamics altering the comparison.
9. First compare Legacy drive on A/B; then switch both to Cascaded. Start Stage
   Gain 12 dB, Interstage Cut 6000 Hz, Trim 0 dB. Adjust stage gain/cut/trim,
   auditioning both with and without Flextron. Bypass only one comparison track
   at a time to avoid comb filtering. Document Flextron settings/version.
10. For every A/B use post-chain track trim to match integrated loudness over
    the same passage, then fine-tune by ear at a conservative monitoring level.
    Do not equate peak matching with perceived loudness. Record trims and meter
    readings; added compensation is a starting point, not automatic matching.
    Compare attack, pitch clarity, chords, high-string fizz and low-string
    definition. Require a listening verdict before saying tone/definition improved.
11. Play/record a sustained lead note (at least 5–10 seconds) identically through
    each path, including near-silent tail and between-note noise. Compare time
    to fall 20/40 dB below initial level, tail roughness, noise floor and apparent
    sustain at matched onset loudness. Existing distortion can change decay;
    there is no new compressor, gate, attack/release control or sustain promise.
    Record desired sustain/noise behavior for a later dynamics PR.
12. Test all enables, Master Bypass, both selectors and rapid automation, including
    mode reversal mid-crossfade. Confirm no disruptive bursts/clicks. Repeat the
    above at 44.1/48/96 kHz, then other device rates and block sizes. Check left
    and right isolation, sample-rate changes, render/live consistency and CPU.
    High-drive aliasing is expected; report it rather than claiming elimination.

### Runtime result status

No REAPER executable is available in this development workspace. v0.2 compilation,
side-by-side host insertion, listening, CPU, and perceived-loudness/lead-decay
checks are **pending**, not passed. v0.1 was reported working by the user and
merged before this issue; that does not validate v0.2. Do not merge this PR until
host tests are recorded. Compressor/sustainer scope is deferred to a separate PR
as permitted by Issue #2, after filter/drive behavior is validated.

Development run on 2026-11-17: **23 automated test cases passed** (the prior 14
plus nine v0.2 cases); compatibility checks inspect both JSFX files. Diff
whitespace checks passed. The v0.1 blob SHA matches merged main:
`442fee3dc5c81beb6f7269381dbf5b840d948d32`.
