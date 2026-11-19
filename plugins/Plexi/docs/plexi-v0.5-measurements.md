# Plexi v0.5 baseline and comparison measurements

Baseline v0.4 native rendering was established before the new production file
was created. Final reproducible fixtures use odd FFT bins to avoid low-order
folded harmonics coinciding with valid harmonic bins. The baseline and final
version were rerun with those identical fixtures. No original file is changed.

## Method

Actual REAPER 7.47 Linux batch execution, stereo amplifier with cabinet bypassed,
original default amp controls. Left channel receives synthetic coherent stepped
sines near 200/1000/3000/6000/10000 Hz at amplitudes 0.00001/0.01/0.1/0.5;
right channel is zero and is checked for crossfeed. Each segment has 0.7 seconds
of settling followed by 8192 measured samples. Input is 32-bit PCM; host batch
output is 24-bit PCM. Input levels are normalized peak amplitudes, not guitar
pickup voltages. Tiny-input output is near the quantization floor; reported
small-signal differences have that precision limit.

`nonharmonic_db` sums spectral energy outside DC and the legal below-Nyquist
harmonic bins (with one neighboring bin excluded each side), relative to the
fundamental. This is a folded-energy proxy, including noise, quantization and
residual transients, **not an exact alias-only decomposition or perceptual score**.
Odd-bin coherent stimuli avoid common alias/harmonic collisions. Per-segment
fundamental amplitude, H2–H8 where below Nyquist, peak and this proxy are saved.

Original memoryless preamp/phase/power/safety primitives are also measured at
all three rates and three input amplitudes. Their curves are evaluated directly
from original equations; no interstage filtering, rail envelope or circuit
loading is represented by that diagnostic. Full amplifier measurements above
execute the actual JSFX with those interactions.

## High-input folded-energy proxy (0.5 amplitude)

More-negative dBc is less nonharmonic energy. This table shows actual coherent
frequencies closest to 3/6/10 kHz; all input levels/frequencies and harmonics
are retained in the JSON files.

| Host rate | Approx tone | 1x dBc | 2x dBc | 4x dBc |
| --- | --- | --- | --- | --- |
| 44100 | 2998.5 Hz | -16.2 | -29.0 | -45.3 |
| 44100 | 6002.4 Hz | -11.9 | -20.3 | -30.5 |
| 44100 | 10007.6 Hz | -7.5 | -14.9 | -23.0 |
| 48000 | 3005.9 Hz | -17.7 | -29.4 | -36.5 |
| 48000 | 6005.9 Hz | -13.6 | -22.6 | -31.1 |
| 48000 | 10002.0 Hz | -7.9 | -15.8 | -25.2 |
| 96000 | 3011.7 Hz | -29.4 | -46.3 | -51.2 |
| 96000 | 6011.7 Hz | -22.0 | -31.3 | -45.7 |
| 96000 | 9996.1 Hz | -15.2 | -24.7 | -35.2 |

## Peak output and batch cost

Times include process startup, decoding and output I/O; not portable CPU usage
percentages. Runs on a shared machine have scheduling variability. These sweep
runs have cabinet bypassed; separate stream tests exercise a maximum-size cabinet.
No hard deadline or listening conclusion follows from a fast offline render.

| Host rate | Audio seconds | v0.4 render s | v0.5 Off s | 2x s | 4x s | v0.5 peak Off/2x/4x |
| --- | --- | --- | --- | --- | --- | --- |
| 44100 | 18.01 | 1.79 | 1.67 | 2.31 | 4.69 | 0.1986/0.2117/0.2142 |
| 48000 | 17.71 | 1.12 | 1.20 | 2.50 | 5.04 | 0.1986/0.2107/0.2105 |
| 96000 | 16.01 | 1.71 | 1.83 | 4.10 | 8.49 | 0.1988/0.1993/0.1991 |

On Linux the benchmark also records child-process **user+system CPU seconds**
via standard-library `resource.getrusage(RUSAGE_CHILDREN)`, excluding parent
Python analysis. This includes REAPER startup/render/I/O CPU across its threads;
it is not audio-thread CPU or an instantaneous device callback utilization.
On platforms without `resource` that field is null rather than estimated.

| Host rate | v0.4 process CPU s | v0.5 Off CPU s | 2x CPU s | 4x CPU s |
| --- | --- | --- | --- | --- |
| 44100 | 1.30 | 1.14 | 2.08 | 4.42 |
| 48000 | 0.88 | 0.99 | 2.31 | 4.73 |
| 96000 | 1.42 | 1.60 | 3.91 | 8.27 |

The initial generic FIR version took about 12.0 seconds at 4x/96 kHz for this
16-second stimulus. The final polyphase version took about 8.2 seconds with the
same measured output. This is a development comparison, not a cross-machine CPU
promise. Off's spectral records equal v0.4 exactly. Higher-mode gain/phase and
harmonic differences are real and are not normalized away.

## Small-signal fundamental change versus v0.4

Values in dB at approximately 200/1000/3000/6000/10000 Hz respectively:

| Host rate | Mode | Changes in dB |
| --- | --- | --- |
| 44100 | 2x | +0.09, +0.14, +0.06, -0.31, -1.18 |
| 44100 | 4x | +0.14, +0.21, +0.12, -0.35, -1.48 |
| 48000 | 2x | +0.08, +0.13, +0.06, -0.26, -1.01 |
| 48000 | 4x | +0.13, +0.20, +0.12, -0.29, -1.26 |
| 96000 | 2x | +0.04, +0.07, +0.06, -0.03, -0.24 |
| 96000 | 4x | +0.06, +0.10, +0.09, -0.02, -0.28 |

## Raw records and reproduction

- [v0.4 native baseline](measurements/v0.4-baseline.json)
- [v0.5 native spectral comparison](measurements/v0.5-spectra.json)
- [v0.4 memoryless primitive diagnostics](measurements/v0.4-primitives.json)

From the repository root, supply your own REAPER. Spectral/primitive analysis
requires NumPy (development only); standard regression/native stream runners use
Python's standard library. No Python package is required by the JSFX.

```console
python3 plugins/Plexi/tests/measure_oversampling.py --reaper /path/to/reaper --report /tmp/v04.json
python3 plugins/Plexi/tests/measure_oversampling.py --reaper /path/to/reaper --source plugins/Plexi/jsfx/Bostone_Plexi_v0.5.jsfx --modes 0,1,2 --report /tmp/v05.json
python3 plugins/Plexi/tests/measure_nonlinear_primitives.py --report /tmp/primitives.json
```

The [test checklist](plexi-v0.5-testing.md) separates automated/native evidence
from pending Windows live audio and listening. No Flextron matching or Boston
recording comparison was performed or used as a target.

## Maximum-capacity cabinet stream cost

Thirty-second streams, original default gains, amp and cabinet enabled. Elapsed
64-frame probe maxima are shown **without discarding scheduler outliers**. They
are observed wall-time maxima, not worst-case audio-thread CPU execution time;
on this shared host they exceed nominal device budgets, so these data cannot
certify real-time deadlines. Windows RT measurements remain required.

| Host rate | Mode | 30 s batch render time | Largest observed 64-frame elapsed time |
| --- | --- | --- | --- |
| 44100 | 1x | 3.28 s | 2.086 ms |
| 44100 | 2x | 5.41 s | 3.005 ms |
| 44100 | 4x | 9.18 s | 5.294 ms |
| 48000 | 1x | 3.89 s | 5.336 ms |
| 48000 | 2x | 6.44 s | 7.115 ms |
| 48000 | 4x | 9.89 s | 16.363 ms |
| 96000 | 1x | 6.51 s | 4.410 ms |
| 96000 | 2x | 11.57 s | 8.598 ms |
| 96000 | 4x | 19.29 s | 4.929 ms |

No periodic silent output windows were detected in those renders. The fixed
operation bounds and one-load counters are evidence against added periodic
work, not proof that an audio device will never underrun.
