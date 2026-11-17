# Validation

## Automated offline checks

From the repository root with Python 3.9+:

```console
python -m unittest discover -s tests -v
```

The harness is an independent numerical model in `tests/offline_dsp.py`, not a
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
