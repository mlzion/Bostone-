# Plexi v0.5 validation and Windows listening checklist

## Reproduce automated tests

From the repository root, Python 3.9+:

```console
python3 run_tests.py
python3 run_tests.py --plugin Plexi
```

The added tests freeze v0.3/v0.4 source hashes, the original 19 sliders and
unchanged cabinet functions/sample/serialization/GUI code. They check FIR gain,
pass/stop bands, zero-stuff/polyphase equivalence, round-trip delays, memory
regions, rate coefficients, switch policy and saved measurement expectations.
Saved-data tests validate recorded evidence, not a new execution of REAPER.
The shared syntax check is conservative lint, not an EEL2 compiler.

Actual-source optional native runners (supply your installed REAPER executable):

```console
python3 plugins/Plexi/tests/run_reaper_oversampling.py --reaper /path/to/reaper --seconds 30 --report /tmp/host.json
python3 plugins/Plexi/tests/run_reaper_latency.py --reaper /path/to/reaper --report /tmp/latency.json
```

The stream runner exercises default 1x/2x/4x at 44.1/48/96 kHz, cabinet bypass,
amp bypass with maximum-capacity cabinet, amp+cabinet, and fast target automation.
The 96 kHz cabinet is requested-rate-converted from a 48 kHz WAV; cabinet input
rates remain 44.1/48 kHz. Each channel has distinct input/IR coefficients. Guards
check amp/FIR/cabinet memory boundaries, IR-load count and ready status. A separate
low-level L-only sine checks mode changes/crossfeed without high-drive waveform
edges. There is no added diagnostic output in the production plugin.

Rapid mode/gain/EQ target tests operate on the same production targets as @slider;
they do not automate REAPER's graphical sliders. Extreme pre/power drive creates
steep saturated waveform edges even in v0.4. Those tests compare peak sample
steps with an identically automated v0.4 reference, rather than interpreting
every steep edge as an audible click. Low-level mode-only tests impose a separate
0.0005 maximum absolute step. Passing these bounds does **not** establish inaudible
switching, and the documented brief dry transition is expected.

The identity runner replaces only the amplifier function in a temporary test
copy, leaving real resampling/PDC code. It compares every output sample against
independent zero-stuff/FIR/decimation and verifies compensated impulse peaks.
It validates the converter's declared 48-frame alignment plus cabinet delay,
not the frequency-dependent phase of a nonlinear amplifier.

Stream timing probes measure maximum elapsed wall time across 64 processed frames.
This is a batch proxy including Linux descheduling, timer overhead and possible
host work between samples. It is not a measurement of Windows audio callbacks,
thread CPU time or a hard real-time upper bound. Inspect raw maxima, do not infer
that average render throughput certifies deadlines or zero live underruns.

## Windows REAPER checklist (pending user execution for v0.5)

The user's Windows continuous-playback/cabinet-switching confirmation applies to
**v0.4**. Native tests in this work use REAPER 7.47 **Linux**, not Windows listening.

1. Install v0.5 alongside the unchanged versions. Confirm the display name and
   all original sliders/defaults, then the new Off/2x/4x slider. Start with low
   monitor volume and keep whole-FX oversampling disabled during this comparison.
2. Use the same clean DI, output level and IR as v0.4. First bypass both cabinets,
   keep v0.5 Off, and compare rendered tracks with REAPER PDC enabled: expect a null.
   Without PDC, v0.5 adds 48 samples compared with v0.4. Also null amp-bypassed
   tracks with the same cabinet, raw mode and cabinet gain/filter settings.
3. Enable the same internal cabinet. Keep the 4096-processed-frame limit and
   original Data/BostoneIR folder. Test valid mono/stereo, missing and repaired
   files, explicit crop, cabinet bypass, saving/reopening and stopped-transport
   cabinet replacement. Mode changes must not request/reload the IR. Do not assume
   uninterrupted live file I/O; the v0.4 load policy is preserved.
4. Compare Off/2x/4x with identical inputs and settings. Listen for fizzy folded
   highs, pick attack, volume-knob cleanup, low-frequency tightness, Presence,
   sustained tails and perceived level. First preserve exact gains; then, if useful,
   do a separate level-matched listening pass. Record subjective differences;
   no Flextron or exact historical amp matching is a development target.
5. Change modes while stopped, then test playing mode transitions cautiously.
   Expect fade to dry, priming and fade back, not a seamless dual-amp crossfade.
   Check impulses/clicks, level surges and stale tails. Toggle Amp/Cabinet Enable;
   verify exact steady bypass apart from fixed latency. Rapid controls should
   remain finite, but test guitar waveforms as well as quiet sines.
6. At 44.1/48/96 kHz run each mode for at least **60 seconds**, then several minutes
   with your longest accepted IR. Test device buffers 64/128/256 frames. Record
   RT CPU, maximum callback time if available, underruns/dropouts and other system
   load. 4x/96 kHz is demanding; choose a lower mode when headroom is insufficient.
7. Stop playback before device-rate changes. Verify reinitialization, IR conversion,
   PDC and output after the change; reopen the project and confirm mode/IR recall.
   Check offline renders versus live monitoring. No live-rate-switch behavior
   was certified by separate Linux batch process tests.
8. Monitor peaks with high input/pre/power gains and output near 0 dB. The
   decimator and IR can overshoot the original pre-decimation ceiling. No new
   limiter or normalization conceals peaks; preserve monitoring headroom.

Do not merge automatically. Treat v0.5 as experimental pending these listening
and real-time checks. [Design/tradeoffs](plexi-v0.5-oversampling.md) and
[baseline data](plexi-v0.5-measurements.md) explain the measurable differences.

### Invalid-input diagnostic

`run_reaper_oversampling.py --dynamic-only --inject-invalid --seconds 10`
(with the same `--reaper` and `--report` arguments) injects infinity/NaN test
expressions into temporary input code. A latched pre-PCM finite-output guard
shares the memory-canary diagnostic channel, so integer WAV conversion cannot
hide a non-finite output. Six native cases cover both fast-target and low-level
mode-only stimuli across all three rates. This instrumentation is not shipped
in the production plugin.

## Recorded results — 2026-11-19

- **58 standard-library tests passed**: 29 Plexi, 24 unchanged Preamp and five
  unchanged shared compatibility cases. Seven new cases cover v0.5.
- **33 native REAPER 7.47 Linux stream cases passed**, 30 seconds each, eleven
  per host rate: amp/cabinet/combined at all three modes, rapid mode/gain/EQ/
  bypass targets, and low-level mode-only transitions. No detected 1024-frame
  silent windows in steady/default streams; mode-only 100 Hz streams remain
  active through switching. All memory guards, IR readiness and single-load
  checks passed. Off amp and amp-bypassed cabinet comparisons to v0.4 are exact.
- **Nine native identity/PDC cases passed** (all three modes/rates), direct FIR
  errors below 0.000002 and compensated impulse peaks at the expected frames.
- **Six native invalid-input cases passed**, ten seconds each: infinity/NaN
  injection, pre-PCM finite-output latch, fast-target and low-level mode changes.
- **12 native spectral sweep renders** (three v0.4 and nine v0.5) completed;
  all use default amp settings with cabinet bypassed. Right channel remains
  silent. Tiny-signal response, harmonics, folded-energy proxy, output peaks,
  batch wall times and actual child-process CPU seconds are recorded.
- All prior five JSFX files retain their hashes; Preamp/shared projects are
  untouched. Local documentation links and staged whitespace checks pass.

These counts describe separate tests, not 60 Windows real-time/listening runs.
Stream/identity/invalid diagnostics use temporary source copies; spectral
renders compile the uninstrumented production files. The 30-second stream
records were captured before adding the pre-PCM finite latch to the runner;
the separate six invalid-input tests use that latch. Production source is the
same final version in both runs. Integer WAV finiteness alone is not a NaN test.

Raw evidence: [native streams](measurements/v0.5-native-stream.json),
[PDC/identity](measurements/v0.5-latency.json),
[invalid inputs](measurements/v0.5-invalid-input.json),
[measurement manifest](measurements/README.md) and
[spectral/CPU report](plexi-v0.5-measurements.md).

Maximum low-level mode-only steps are approximately 0.000263 / 0.000229 /
0.000080 at 44.1/48/96 kHz. High-drive automation steps are 0.374 / 0.364 /
0.252, versus v0.4's 0.371 / 0.361 / 0.243; they remain within 10% of the
same extreme-target reference and do not demonstrate inaudibility.
