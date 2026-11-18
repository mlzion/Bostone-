# v0.4 convolution design and reference research

## Investigation before implementation

The official references were reviewed before coding:

- [JSFX file I/O / serialization](https://www.reaper.fm/sdk/js/file.php): native
  file slider/open, media metadata, bounded reads, file errors, saved strings,
  and REAPER 6.29+ requested-rate decoding via file_riff with the 'rqsr' flag.
- [File sliders / sections](https://www.reaper.fm/sdk/js/js.php) and
  [string functions](https://www.reaper.fm/sdk/js/strings.php): a Data-subfolder
  selector and filename extraction; no arbitrary native Browse dialog is assumed.
- [FFT and memory APIs](https://www.reaper.fm/sdk/js/advfunc.php): complex pairs,
  permutation/inverse permutation, inverse scaling and 65536-item page limits.
- [PDC, transport and sample rate](https://www.reaper.fm/sdk/js/vars.php): declared
  channel latency, stopped-transport loading policy and initialization lifecycle.
- [Official Cockos effects guide, ReaVerb sections 15.1/15.3/15.5/15.6/15.8](https://www.reaper.fm/userguide/REAPEREffectsGuide2021.pdf): separate impulse normalization/attenuation, wet/dry, filtering and length modules.

All engine/test code is original. No third-party JSFX, cabinet IR, proprietary
ReaVerb implementation, WAV asset, or GPL/LGPL code is imported. Synthetic WAVs
are generated temporarily by tests. General FFT/convolution mathematics and
published API semantics are used, not copied DSP implementations.

## ReaVerb: what is known and what is not

The official effects guide explicitly distinguishes impulse normalization from
attenuation; it does not enumerate every label/formula of the File dropdown.
The separately documented Normalize module adjusts impulse peak level. Therefore
an unspecified reported '-18 dB' choice cannot safely be treated as a single
output trim. This prototype exposes unambiguous choices instead of claiming an
unmeasured exact match to every ReaVerb dropdown item:

| v0.4 mode | Exact processing |
| --- | --- |
| Normal Raw | Original resampled FIR, no peak normalization |
| Apply -18 dB | Raw FIR times 10^(-18/20) |
| Peak Normalize 0 dBFS | FIR divided by its linked stereo maximum absolute sample |
| Peak Normalize -18 dBFS | FIR divided by linked stereo peak, then times 10^(-18/20) |

Silent impulses stay silent; no division by zero. The normalization peak is
measured AFTER requested resampling and explicit crop, BEFORE wet filtering.
One peak across both channels preserves their relative balance. IR Level is an
independent smoothed wet-only multiplier. Raw is the default: no automatic
compensation for arbitrary IR strength.

A fixed -18 dB multiplier and normalization to -18 dBFS are different operations
unless the original peak happens to be 1. Do not assume which option the user
selected in ReaVerb; record its exact label/build and measure with known impulses.
Raw, same-rate, filters-off convolution should agree mathematically after engine
latency alignment; no ReaVerb null or listening test has been performed.

ReaVerb's decoder/SRC details, stereo normalization policy, filter topology,
filter placement/tails, length processing and ZL/LL scheduling are not fully
specified by those docs. No exact matching claim is made for them. v0.4 supplies
wet-only one-pole HP/LP (0 = off), smoothed coefficient updates and 10 ms filter
bypass ramps. This is a stated approximation to ReaVerb filtering, not an
asserted slope/phase match. Optional length is a simple truncation, not ReaVerb's
time stretch, fade, reverse, pre-silence or arbitrary module chain.

Stereo is intentionally diagonal for channel isolation. When comparing ReaVerb,
disable mono mixing, pan/width alterations, offsets and extra modules; verify
routing with L-only and R-only impulses. Four-channel true-stereo files are
unsupported rather than remixed. Raw-mode fidelity is prioritized over UI mimicry.

## Nonuniform partitioned overlap-add (continuous-audio correction)

The original uniform engine's interpreted complex multiply loop ran even in
cabinet bypass and exceeded the three-second audio duration in a near-capacity
native render on the development machine. No fixed one-second gating operation
or overlapping memory region was found. Offline old-code rendering stayed
continuous; the Windows live failure is not claimed reproduced. A measured
real-time-budget problem was addressed rather than assuming an indexing defect.

The replacement uses B=64/N=128 for the first 256 FIR taps, then B=256/N=512
for the remaining taps beginning at IR offset 256. Each bank uses zero-padded
partitioned OLA: Y_j=sum(X_(j-p)*H_p). Native convolve_c performs complex products;
a small unrolled addition loop accumulates them. Inverse results are divided by
the actual FFT length N; the second half is saved as overlap. No STFT window.

The head output retains 64 samples of algorithmic delay. The tail engine has
256 samples of algorithmic delay plus a separate 64-sample output delay:
256+64 = original IR offset 256 + global latency 64. Thus taps on both sides of
255/256 and every later boundary retain their exact time/gain. There is no gap,
double-counted boundary or arbitrary tail shift. Native delta/multitap and
continuous-stream comparisons validate this schedule.

Both channels have separate spectra, overlap and audio histories. Shared FFT
workspaces are used sequentially; the right channel cannot overwrite the left
output. The independent dry ring always advances once per sample, outside all
FFT, bypass and file-loading branches. Its memory is never cleared on IR swap
or cabinet re-enable. Global latency/PDC stays 64 in every cabinet mode,
including bypass/no IR: about 1.45 ms at 44.1 kHz or 1.33 ms at 48 kHz.

After the existing 10 ms bypass fade completes, cabinet FFT work is suspended.
Re-enable resets/re-primes only convolution/filter histories while the dry ring
continues. The unchanged dry path carries audio until the head is primed and
then the existing fade engages the cabinet. Old bypass-era tails are discarded,
not replayed. This deliberately replaces the former expensive warm-FFT policy.

## Resampling and gain

REAPER decodes native 44.1/48 kHz WAVs and supplies requested-rate samples before
any audio reads. For non-normalized modes the converted FIR is multiplied by
source_rate/processing_rate: ordinary audio SRC preserves sample amplitudes,
whereas FIR coefficients need area correction to keep their low-frequency gain
consistent when the sample density changes. This is resampling math, not
arbitrary loudness normalization. At equal rates the multiplier is 1. Peak modes
explicitly replace this gain with the requested linked-peak scaling.

Host SRC is a black box. The offline oracle uses an independent windowed-sinc
resampler to test expected duration, delay and coefficient-sum behavior; it does
not replicate REAPER's exact interpolation kernel, output frame rounding or edge
treatment. Same-rate raw comparison should be tested first. Resampled ReaVerb
parity remains a host measurement requirement.

## Memory and CPU

Amp memory remains [0..88]. The dry L/R rings remain [1920..2047]. The head's
256-slot FFT/work buffers start at 1024/1280, followed by its disjoint 64-frame
input/output/overlap buffers. Tail FFT/work buffers start at 4096/5120 (1024
slots each), tail audio buffers at 6144..7679, and alignment rings at 7680..7807.

Head H L/R and X L/R banks start at 65536/66560/67584/68608, reserving four
256-slot partitions each. Tail H L/R and X L/R banks start at
131072/262144/393216/524288, reserving 128 partitions of 1024 slots each. The
maximum tail uses 127 partitions. Raw data remains at 655360..720895. All FFT
slots fit wholly within a 65536-item page; regions never overlap. Highest raw
endpoint remains 720896, about 5.5 MiB at eight bytes per slot. Reset clears
convolution/filter buffers, never amp matrix or the continuous dry delay.

Source-derived interval tests validate the actual constants, and native-host
test-only canaries at critical region boundaries remain unchanged. The tests
also check that each run loads its IR once, and FFT call counters stop throughout
settled cabinet bypass. These diagnostics are not production features.

The tail's per-second partition work drops by roughly fourfold, and complex
products run in REAPER's native primitive instead of interpreted arithmetic.
Render wall times for three seconds of 48 kHz stereo with a 32768-frame IR were
about 4.23 s before, versus 1.25–1.36 s enabled / 0.62 s bypassed after correction
on this environment (including startup/I/O). These are not portable CPU-percent
or hard real-time guarantees. Small device buffers, long IRs and oversampling
still need Windows real-time CPU/xrun tests. No data asset/REAPER binary is bundled.

## Loading, persistence and state transitions

The native dropdown supplies a filename. Explicit serialization stores the name
(or its resolved Data-relative path), not only its numeric menu index. On restore
the saved string takes precedence over the first restored menu notification.
External audio is never embedded. Files must remain accessible; errors produce
aligned amp-only output and status rather than stale audio, silence or a crash.

IR or processing/length changes queue during playback. When transport stops,
the cabinet mix ramps to unity amp bypass over 10 ms, then synchronous decoding
and FFT preparation occur in @block. Coefficients/history are reset; only after
the first processed block is primed can cabinet mix ramp back in. Existing dry
alignment history is retained on replacement. Initial/rate/transport @init keeps
the original amp reset behavior and permits saved IR preparation before the
first block, even if playback is beginning. File I/O is never in @sample or @gfx.

The same 20 ms amp smoothing constant is reused for cabinet gain/filter targets;
bypass/filter mixes use its 10 ms ramp. Reload is fade-to-bypass and fade-back,
not simultaneous old/new IR convolution. It cannot guarantee no audio underrun
from disk reads. Mute monitoring for changes. FFT/non-finite/extreme-output
faults disengage the cabinet; the amp itself remains unchanged. No output limiter
is appended because that would change IR gain/tone. Linux 7.47 batch validation is recorded in the testing notes. Windows live
monitoring, GUI reload clicks and device-buffer/xrun behavior still need retesting.
