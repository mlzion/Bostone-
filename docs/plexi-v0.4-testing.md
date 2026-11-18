# v0.4 cabinet validation

## Automated suite

From the repository root, Python 3.9+:

```console
python3 -m unittest discover -s tests -v
```

The existing suite plus new cabinet cases cover:

- Full v0.3 amp function/slider/init/sample-source preservation and v0.3 blob hash.
- FFT partition boundaries, leading-silence timing, impulse gain and fixed latency.
- Stereo convolution against direct time-domain FIR on seeded random signals;
  zero crossfeed and mono coefficient duplication.
- 44.1/48 kHz conversion in both directions and higher processing rates;
  duration, delay and FIR area/gain correction.
- Distinct fixed attenuation and linked peak-normalization modes, silent IR,
  IR level and wet/dry algebra, filters and smoothed control transitions.
- Explicit crop/capacity checks; synthetic mono/stereo PCM WAV reads, missing,
  corrupt, unsupported and non-finite data; filename-based persistence contract.
- Silent input, exact latency-aligned cabinet bypass and amp→cabinet bypass
  pipeline; finite output; FFT page boundaries and memory capacity.

These are independent numerical/source checks, not EEL2 execution. Python's
fixture PCM reader, FFT and windowed-sinc oracle are not REAPER's decoder, FFT,
resampler or project-state system. Valid PCM/float WAV codec coverage, GUI menu
behavior, actual persistence and load-state race behavior remain host tests.
Existing amp tests are retained; a source contract confirms its definitions,
original controls and processing section are unmodified in the new file.

## Mandatory REAPER checks — pending

Runtime compilation and audible tests are deliberately separate. No REAPER
executable is installed here; no host or listening test below has been performed.

1. Install using [the usage instructions](plexi-v0.4-cabinet.md). Confirm the
   distinct FX identity, all ten original amp sliders/defaults and appended
   cabinet controls; open Edit and verify compilation before routing monitors.
2. With Cabinet bypassed, compare v0.4 against v0.3 after aligning the 64-sample
   delay (or letting host PDC align rendered tracks). Null both amp-active and
   Amp-bypass cases. Test sample-rate/transport changes and save/reopen recall.
3. After loading, let at least 150 ms of silence pass for cabinet/filter/gain
   ramps to settle before accuracy measurements. Use generated delta WAVs and known offsets, not copyrighted IR assets, for
   accuracy: mono delta 0.5, delayed delta, different L/R deltas, and a short
   multitap file. Compare against ReaVerb at matching raw/normal, wet 0 dB,
   dry muted, IR gain unity, filters disabled and no extra modules. Align latency
   and compare tails. Verify L-only input never appears on R and vice versa.
4. Record the exact ReaVerb File-dropdown labels/build. Measure fixed -18 dB and
   peak normalization to -18 dBFS with a 0.25-peak fixture: these must produce
   different results. Compare the corresponding explicit v0.4 modes. Also test
   stereo unequal peaks and silent files; do not infer normalization from a label.
5. Repeat native-rate WAVs at 44.1/48 kHz projects, then mixed rates and host
   oversampling. Record resampling differences rather than assuming an identical
   kernel/gain policy. Keep lengths inside the processed-frame limit; confirm
   an over-capacity file is rejected unless an explicit short crop is selected.
6. Sweep IR Level, wet/dry, HP/LP and Cabinet bypass. Filters affect wet only;
   no-IR and cabinet bypass ignore these controls and remain unity amp output
   after 64 samples. Check the 10/20 ms transitions and no unexpected bypass
   level compensation. Peak overs may be legitimate IR gain; monitor quietly.
7. Change IRs during playback: old sound must continue and status must queue.
   Stop transport, mute monitoring, and confirm fade/load/re-prime/fade-back.
   Test missing/deleted/replaced/corrupt WAV, unsupported rate/channel count,
   short/truncated data, zero IR, transform overflow and recovery using Reload.
8. Save/reopen a project, change the directory's filename ordering, and verify
   the saved filename—not its old menu index—is restored. Test project load
   while playback starts, preset/undo restoration, and files moved to a new
   machine. The WAV is external; missing files should clearly bypass, not pick
   a different listed IR. Verify the status filename and native list refresh.
9. Test 1x/2x/4x, device-rate changes, render/live consistency, block sizes and
   CPU at 20/200 ms and near-limit IR lengths. Higher rates increase partitions
   and shorten supported duration. Do not claim uninterrupted live loading.
10. Compare user cabinet sound against v0.3→ReaVerb with the same external WAV
    and carefully matched processing mode, crop, gain, wet/dry and filter settings.
    Disable any second cabinet elsewhere in the chain; level-match before
    evaluating tone. No cabinet waveform display or custom skin is included.

The PR stays unmerged until review. Long reverb IRs, arbitrary-folder browsing
and more demanding hot-swap requirements are better served by v0.3 + ReaVerb.

## Recorded development results — 2026-11-18

- Complete suite: **41 tests passed** (32 retained baseline/amp/preamp cases plus
  nine cabinet cases), using `python3 -m unittest discover -s tests -v`.
- `git diff --cached --check`: passed.
- v0.3 source identity and original amp sections/sliders are preserved; native
  FFT, decoder, requested-rate SRC, selector/persistence and reload lifecycle
  remain explicitly unverified in REAPER.
- No WAV assets are committed; tests generate temporary PCM fixtures.
