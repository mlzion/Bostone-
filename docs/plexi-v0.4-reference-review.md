# Supplied JSFX reference review — 2026-11-19

Reviewed the user-supplied `Plexi_JSFX_References.zip` locally. These are reference
files, not production dependencies. No source, embedded IR, drawing or asset
from the archive is copied into Bostone. Its README flags LGPL for Cockos/Tukan;
chokehold attribution/licensing requires separate verification before reuse.

| Supplied file | What was reviewed | Practical conclusion |
| --- | --- | --- |
| cockos-amp-model | File-change cache, bounded IR, one FFT overlap/add arrangement, native spectrum multiplication, rate/gain correction | Simple bounded state and cached preparation are useful design principles. Its large transform/chunk choice is not automatically a low-monitoring-latency solution. This is a linear convolver, not a physical amp model. |
| cockos-amp-model-dual | Independent IR loading and channel paths | Keep routing and per-channel histories explicit; do not infer true stereo or isolation from a preset label. |
| chokehold-cabinet_sim.jsfx | Embedded responses, real FFT packing, direct head plus FFT remainder, native complex products, buffer allocation | Packed real FFT halves spectral storage/work, but DC/Nyquist, final bin and normalization must be validated in our host. Its embedded IRs and implementation are not imported. Its scheduler is not reused. |
| tukan-guitar-amp.jsfx | Bias/polynomial nonlinear stages, EQ, copied-attributed convolution subsystem | It offers behavioral ideas, not independently verified historical tube specifications. No polynomial coefficients or LGPL implementation are adopted. |
| chokehold-amp_sim.jsfx | Pre/post shaping, nonlinear-stage-focused oversampling, rate-safe coefficient updates, envelopes and dynamic voicing | Profile nonlinear processing separately from dynamics/cabinet. More stages or controls are not evidence of a more accurate Plexi. |

Review identity (SHA-256, in archive order/name):

- `cockos-amp-model`: `e96384bf512e4a6f332006affe6828ad423132cec996b2e56717c67833c59618`
- `cockos-amp-model-dual`: `c18619dce879db677c6cb9ccfabb04d57190e2ba2cd5115ea1c06e7fcc63c47c`
- `tukan-guitar-amp.jsfx`: `d0af74f41785ecbb057e4f2dd8db9c43d125ff7c2c5373029ffb130b3090a0da`
- `chokehold-amp_sim.jsfx`: `427b72f8efc68347704253d08101735b3bc6ff11fc334355312341504336376e`
- `chokehold-cabinet_sim.jsfx`: `c338cedd06dc973f959d81bb85f57f0938e8c14e0d87ec1a74e65bd341d7d87e`

## Cabinet decision for PR #6

The previous nonuniform tail creates a much larger individual task every 256
samples, while small audio device blocks may provide only 64 samples of deadline
budget. Faster average rendering does not prove that the largest callback fits.
We replaced that schedule with a fixed 128-point real FFT / 64-frame partition
engine, capped at 4096 processed taps (64 partitions). There is no second tail
scheduler or long-period work queue. Native `convolve_c` handles spectral
products; it does NOT provide file loading, history scheduling or a complete
ReaVerb-style convolution engine.

All packed bins are handled explicitly: DC/Nyquist as real values, an even group
of ordinary complex pairs through the native routine, and the final pair
separately. REAPER's packed-real convolution scale was calibrated against actual
host output (two forward transforms plus inverse: 4*N, thus divide by 512 for
N=128), rather than assuming complex-FFT scaling. Direct-FIR comparison catches
both gain and final-bin errors. This is independent mathematical/API work, not
reuse of a reference implementation.

There is also an avoidable reload path in the old serialization policy: any
read requested an IR reload, even when the filename was unchanged. Read/write
mode is now captured before I/O, and only a changed filename requests reload.
IR mode/length changes and explicit Reload keep their existing behavior.

The user's cabinet-off + external ReaVerb path remains the reference baseline.
For long IRs or oversampled rates exceeding the live cap, retain that chain.
An oversized IR is visibly rejected, not silently trimmed. At 44.1/48 kHz select
Maximum Length = 80 ms explicitly to fit a longer file, then confirm status says
Loaded and compare tone. Cropping can alter the cabinet response and is not
claimed acoustically identical to the full file.

### Root-cause confidence

Demonstrated source problems: oversized individual convolution work bursts and
unconditional reload requests on same-file state reads. There is no ten-second
counter, unbounded partition history or repeating file-load timer in the engine.
Thirty-second host runs test counters, memory guards and signal continuity,
including simulated same-file restore notifications at seconds 10 and 20.
Those notifications exercise the production restore-decision helper, not a claim
that Windows actually makes those callbacks at that cadence. The exact Windows
scheduler/event that caused the reported one-second silence is not established.
The new design removes both identified hazards and sharply bounds work; user
Windows real-time confirmation is still required. Do not claim the cadence was
fully reproduced or the user retest already passed.

## Future amplifier recommendations — NOT implemented in PR #6

1. **Establish a measured comparison set first.** Use the user's working external
   ReaVerb chain, identical DI and IR, matched perceived loudness, and Flextron's
   cabinet disabled. Record frequency sweeps, input-level/harmonic sweeps, pick
   attack and 5–10 second decays. Keep the cabinet engine and amp changes separate.
2. **Evaluate nonlinear-only oversampling.** The amp reference's selective
   approach is relevant to CPU control. In a later PR, compare 2x/4x for just the
   nonlinear/interstage path, with proper antialias filters and measured latency;
   do not oversample the cabinet/dynamics gratuitously or copy its filter code.
3. **Improve gain/bias behavior from evidence.** Compare asymmetric preamp
   transfer, DC recovery and pickup-volume cleanup against measurements. The
   Tukan polynomial/virtual-valve controls are not a substitute for validated
   device curves. Keep numerical bounds and independently derive any new model.
4. **Treat power dynamics and Presence as separate research.** Current Plexi
   uses a fixed rail-envelope surrogate and feed-forward Presence shelf. Explore
   load-dependent feedback/Presence and transformer/screen effects only with a
   clear circuit target and stability tests. A static cabinet IR does not model
   speaker impedance interacting with the power stage. Do not rename a compressor
   an exact EL34 model or infer historical component values from another effect.
5. **Preserve the interactive passive tone stack.** Generic pre/post EQ examples
   can guide A/B experiments, but three EQ bands are not a reason to replace the
   existing circuit-derived B/M/T network. Compare loaded response and stage
   coupling before adding features.
6. **Avoid masking faults with gates/maximizers.** The references' gates,
   boosters and dynamics are independent effects; they are not dropout remedies
   and should not be bundled into this correction. Hum cancellation, skin and
   extra amp voicing remain out of scope.
7. **Profile callback peaks, not just throughput.** Retain native source tests
   and add Windows live measurements at 64/128/256-frame device buffers. Record
   maximum/percentile callback time and underruns under normal system load,
   alongside audible tests. Offline rendering alone cannot certify real-time
   deadlines.

No amplifier processing, original amp parameter, default or control is changed
by these recommendations. Any adopted idea needs its own review/PR and licensing
check; production DSP must remain independently implemented.
