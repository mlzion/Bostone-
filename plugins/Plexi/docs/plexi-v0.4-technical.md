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

## Bounded uniform real-FFT convolution

The current engine replaces the previous nonuniform head/tail schedule. All
partitions use B=64, N=128 packed-real overlap-add, with at most 4096 processed
IR frames (64 partitions). Each channel computes Y_j=sum(X_(j-p)*H_p).
Native `convolve_c` multiplies an even group of complex pairs; DC/Nyquist
and the final pair are explicit. Two forward real transforms plus inverse use
4*N scaling: output/overlap divide by 512, verified in actual REAPER output.
No permutation, STFT window, tail scheduler or periodic long task is used.

Each 64-frame boundary runs the same bounded stereo work. At maximum capacity,
spectral accumulation touches at most 64*128*2 scalars, versus the previous
127*1024*2 tail burst: approximately 16 times fewer peak accumulation operations.
This is a structural count, not a measured hard-real-time guarantee.

Latency/PDC remains 64 samples in every mode (1.45 ms at 44.1 kHz, 1.33 ms at
48 kHz). Independent histories preserve stereo isolation. The dry delay advances
on every sample outside convolution/loading and is not reset on cabinet swaps.
Settled bypass suspends FFT work; re-enable clears/re-primes wet histories before
the existing crossfade. Original amplifier code and all 19 sliders are unchanged.

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

Amp memory remains [0..88]. FFT work/sum reserve [1024..1151] and
[1280..1407]. Six 64-frame wet input/output/overlap buffers occupy [1536..1919];
dry rings remain [1920..2047]. H L/R and X L/R banks begin at
65536/73728/81920/90112, each reserving 8192 slots. Raw IR data starts at
131072 and ends before 139264. Highest endpoint is about 1.06 MiB at eight bytes
per slot. FFTs fit within 65536-item pages. Source interval checks and native
memory canaries validate separation; no reset touches amplifier or dry memory.

Thirty-second native enabled renders took about 3.21–3.65 seconds here including
startup/I/O. These are throughput measurements, not callback timing or portable
CPU percentages. Profile Windows audio deadlines at 64/128/256-frame buffers.
Long files are rejected unless explicitly cropped; use external ReaVerb for
long IRs rather than increasing this engine's bounded live workload.

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

State read/write mode is captured before serialization I/O. Same-filename reads
no longer request reloads; changed filenames still do. This removes avoidable
synchronous disk/FFT preparation on redundant state notifications. Actual
Windows event cadence has not been measured. See [reference review and root-cause
confidence](plexi-v0.4-reference-review.md) for evidence and future amp proposals.
