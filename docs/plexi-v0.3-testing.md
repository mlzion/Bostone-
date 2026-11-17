# Bostone Plexi v0.3 installation and acceptance

## Install / update on Windows 11, REAPER 7.x

1. Choose **Options → Show REAPER resource path in explorer/finder**. In that
   directory open `Effects/Bostone` (create it if needed). For a normal Windows
   install this is typically `%APPDATA%\REAPER\Effects\Bostone`.
2. Copy only `jsfx/Bostone_Plexi_v0.3.jsfx` there. Do not rename/overwrite either
   existing Bostone file. Plexi has no imports or other runtime files. Check that
   Windows has not appended `.txt` to the filename.
3. In the FX browser use **FX → Scan for new plugins** and search for
   **JS: Bostone Plexi v0.3**. Reopen the browser or restart REAPER if necessary.
4. Add it to a temporary track. Open **Edit** and verify no compiler error. There
   must be ten sliders and a separate identity from both older versions.
5. For updates replace only this file, save settings first, and remove/reinsert
   Plexi in the temporary test project to ensure the disk revision is running.
   Keep old versions and existing projects intact.

## Controls and starting settings

| Control | Range | Default / DI start |
| --- | --- | --- |
| Amp Enable | Bypass / Enabled | Enabled |
| Input Gain | -24 to +24 dB | 0 dB |
| Preamp Drive | 0–36 dB | 6 dB |
| Bass | 0–10 | 5 |
| Middle | 0–10 | 5 |
| Treble | 0–10 | 5 |
| Presence | 0–10 | 4 |
| Power Drive | 0–24 dB | 3 dB |
| Bass Tightness | 0–10 (70–300 Hz) | 5 (about 145 Hz) |
| Output Level | -36–0 dB | -12 dB |

Start monitoring quietly. For Bostone v0.2 output, start Input -12 dB, Preamp
0–6 dB, Power 0–3 dB, Tightness 5–7 and Output -18 dB, then adjust upward.
For a cranked experiment try Preamp 18 dB / Power 12 dB after establishing a
safe monitor level. These are proposals, not listening-approved presets. There
is no watt/voltage calibration. Cabinet convolution comes AFTER the amp.

## Host oversampling: 2x and 4x

Right-click the Plexi name in the track FX-chain list and open **FX instance
oversampling**. Select a target processing rate appropriate to the project:

| Project rate | Approx. 2x target | Approx. 4x target |
| --- | --- | --- |
| 44.1 kHz | Up to 88.2k/96k | Up to 176.4k/192k |
| 48 kHz | Up to 88.2k/96k | Up to 176.4k/192k |
| 96 kHz | Up to 176.4k/192k | Up to 352.8k/384k |

Some builds show multipliers; choose 2x or 4x there. Confirm the effective rate
and menu in your REAPER build: target-rate choices are not fixed multipliers
at every project rate. Apply this to Plexi alone initially, not the whole chain,
so ReaVerb and upstream processors remain a controlled comparison. Host
resampling adds its own latency/filtering and may affect bypass null tests.
No custom oversampling is present; srate-dependent filters/states initialize
at the processing rate. Compare 1x/2x/4x at matched loudness and record CPU.

## Automated checks

With Python 3.9+ from the repo root:

```console
python -m unittest discover -s tests -v
```

The existing numerical and source-lint suite is retained. The new numerical
reference is independent code, not EEL2 execution. It covers silence, low/high
sines, impulse decay, passive network response and pot interactions, B/M/T
corners, stereo isolation/symmetry, output bounds, malformed samples, exact
settled bypass and warm states, controls/ramps, and 44.1/48/88.2/96/176.4/192/384
kHz processing. A pivoting complex AC solver cross-checks the time-domain
capacitor-companion network at warped frequency. Static checks cover section
and slider structure, actual-source compatibility policy, and v0.1 preservation.

Low-level transition bounds use a 0.00001-amplitude 440 Hz sine. A paired warmed-instance check separately bounds the first parameter-induced
step at a higher signal level. Highly clipped
sines naturally have steep sample slopes; these are not evidence of a parameter
click by themselves. Tests do not establish inaudibility or full EEL2 syntax
validity. Recreating the model at a new rate checks initialization math, not
REAPER's transport lifecycle or host oversampling/resampling implementation.

## Manual REAPER checklist — all pending

1. Record REAPER/Windows builds, project/device rate and block size. Confirm
   compilation, ten slider values/ranges, initialization on transport start,
   save/reopen recall, duplicated independent instances and mono/stereo routing.
2. Insert Plexi on a clean DI. Check silence before/after notes, low-level sine,
   high-level sine, impulse/tail and L-only/R-only audio. No runaway, DC jumps,
   silent-channel leakage, non-finite meters or persistent noise should occur.
3. Automate all controls through endpoints and reverse bypass mid-ramp. Listen
   for objectionable clicks, bursts, pot-step noise or stale-state transients.
   Let ramps settle, then null the Amp Bypass output against dry input at 1x.
   Recheck when host oversampling is enabled, allowing for host resampler delay.
4. Raise Preamp and Power independently. Evaluate asymmetric preamp crunch,
   pick attack, cleanup, sustained-note decay, and power-stage feel. Sweep Bass
   Tightness on palm-muted low strings BEFORE the distortion; compare definition
   and excessive thinning/phase coloration. B/M/T should audibly interact.
5. Compare Presence without harshness, excessive DC, or unexpected overall level.
   Wet output ceiling is a sample bound, not a loudness target or true-peak
   limiter; bypass/crossfade can carry higher dry levels. Monitor conservatively.
6. Test the intended chain:
   **Bostone v0.2 → Bostone Plexi v0.3 → ReaVerb (user's Marshall 1960 IR)**.
   Compare against **Bostone v0.2 → Flextron → ReaVerb (same IR)** with
   **Flextron's cabinet simulation disabled**. No IR/plugin/recording is bundled.
7. Use identical aligned DI passages and upstream settings on duplicate tracks.
   Enable one comparison track at a time, with identical ReaVerb wet/dry and IR
   gain. Use post-chain trim to match passage loudness, then fine-tune by ear;
   equal peaks do not ensure equal perceived loudness. Record all settings.
8. Repeat palm mutes, chords and 5–10 second lead decays at 1x/2x/4x. Judge note
   separation, pick transients, fizz/aliasing, sustain and between-note noise.
   Reference recordings may guide subjective tone, but are not measurement
   targets, training data or assets to commit to the repo.
9. Repeat project-rate changes at 44.1/48/96 kHz and effective rates through
   384 kHz; stop playback before changes. Confirm state reset without bursts,
   preset recall, offline render/live consistency and CPU at relevant block sizes.

REAPER is unavailable in this development workspace. No runtime compilation,
Windows installation, actual host oversampling, audio listening, loudness match,
CPU measurement or comparison against Flextron has been performed here. Those
acceptance criteria remain pending; keep the PR unmerged for review and testing.

| Build | Project / effective rate | Block size | Test | Result |
| --- | --- | --- | --- | --- |
| Pending | Pending | Pending | All manual checks | Not performed |

## Recorded development results (2026-11-17)

- `python3 -m unittest discover -s tests -v`: **23 tests passed** — 14 retained
  baseline/compatibility cases and nine Plexi cases. Final run completed in
  about 5.2 seconds on Linux/Python (not a real-time CPU benchmark).
- `git diff --cached --check`: passed.
- Active-path numerical sample ceiling held at 0.8 or lower across the tested
  rates, high inputs and control extremes; fully settled finite bypass was exact.
- The independent AC solver and time-domain tone network agreed at the tested
  warped-frequency point; all tested tone pot corners remained finite.
- REAPER runtime and listening results: **not performed / pending**.
