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

## Uniform partitioned overlap-add

Block B=64, complex FFT N=128. Each FIR partition contains 64 coefficients plus
64 zeros. Each input block is zero padded likewise. In frequency order:

Y_j = sum over p of X_(j-p) * H_p.

After inverse permutation/IFFT, divide by 128; output first half plus last
block's saved overlap, and retain the second half for the next block. No STFT
window is applied. The current block is computed after its last input sample;
its first output appears the next sample, giving exactly 64 samples of engine
latency. Original IR leading silence and timing are additional and untouched.

Each channel has its own FFT history, accumulator, overlap and dry delay. Mono
coefficients are duplicated, not audio channels. Dry output is delayed by the
same 64 samples. pdc_delay=64, pdc_bot_ch=0, pdc_top_ch=2 remains constant in all
cabinet modes, including missing IR and cabinet bypass; no PDC jumps on switches.
This is about 1.45 ms at 44.1 kHz or 1.33 ms at 48 kHz, excluding interface and
host oversampling latency. No zero-latency convolution claim is made.

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

All amp memory remains at its original offsets; cabinet buffers begin at 1024.
FFT work slots use 256 items. IR L/R banks start at 65536/196608, input spectral
rings at 327680/458752, and raw interleaved data at 655360. Each bank has 512
partitions. FFT offsets are multiples of 256 and never cross a 65536-item page.
The highest raw-data endpoint is 720896 slots, about 5.5 MiB at eight bytes per
slot, within JSFX's default local address space. No globals are shared between
instances and no per-sample buffer allocation is performed.

At 48 kHz a 20 ms IR needs 15 partitions; a 200 ms IR needs 150. Work scales
linearly with partitions and processing rate. Two channels need four 128-point
transforms per input block, plus complex multiply/accumulate work. Long IRs and
whole-instance oversampling can be costly; no measured REAPER CPU percentage
is claimed. Memory is bounded and oversize requests fail rather than truncate.

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
is appended because that would change IR gain/tone. Runtime lifecycle, UI/file
persistence, reload clicks and CPU must be validated separately in REAPER.
