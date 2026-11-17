# Signal chain

Both channels follow this identical chain, with shared controls and coefficients
but separate filter histories. There is no channel summing or crossfeed.

1. **Input gain:** amplitude multiplier `10^(dB/20)`.
2. **Pre-EQ:** second-order high-pass, bell, then second-order low-pass.
3. **Distortion:** `tanh(Drive × sample)`.
4. **Post-EQ:** low shelf, bell, then high shelf.
5. **Output gain:** amplitude multiplier `10^(dB/20)`.
6. **Master bypass:** crossfade from the complete chain to the unprocessed input.

| Filter | Frequency | Shape |
| --- | --- | --- |
| Pre high-pass | Low Cut slider | Q = 1/√2 ≈ 0.7071, 12 dB/octave |
| Pre bell | Low-Mid Frequency slider | Q = 1 |
| Pre low-pass | High Cut slider | Q = 1/√2 ≈ 0.7071, 12 dB/octave |
| Post low shelf | Fixed 150 Hz | RBJ shelf slope S = 1 |
| Post bell | Mid Frequency slider | Q = 1 |
| Post high shelf | Fixed 4000 Hz | RBJ shelf slope S = 1 |

Shelf S is a slope parameter, not a constant bell Q. Its alpha is
`sin(w)/sqrt(2)` for S = 1. Bells at 0 dB and shelves at 0 dB are neutral at
steady state. The default pre low/high cuts remain active.

Every enable switch crossfades between its stage's input and output over 10 ms.
Master Bypass On means dry; other Enable switches On mean active. Filters and
parameter smoothers continue running while bypassed to keep histories current.
Fully bypassed master output is exactly dry for ordinary finite inputs; invalid
or pathological inputs are sanitized as described in the DSP notes.

There is no added latency, lookahead, cabinet, chorus, delay, compression,
noise gate, stereo widening, or oversampling in this version. A bypass crossfade
can temporarily change the frequency response because filtered and dry signals
have different phase. This is expected for this prototype.
