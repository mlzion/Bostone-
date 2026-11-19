# Source and algorithm register

All production DSP in `jsfx/Bostone_Preamp.jsfx` was independently written for
Bostone. No third-party JSFX, DSP implementation, cabinet IR, audio recording,
GPL/LGPL implementation, or binary dependency was imported. The test model is
also original project code and uses Python's standard library only.

| Reference | Technique used | Relationship to project code |
| --- | --- | --- |
| Robert Bristow-Johnson, Audio EQ Cookbook; W3C publication: https://www.w3.org/TR/audio-eq-cookbook/ | Bilinear-transform biquad HP/LP, bell EQ, shelves, coefficient normalization, Q and S definitions | Mathematical algorithm reference; no implementation source copied |
| Cockos JSFX programming reference: https://www.reaper.fm/sdk/js/js.php | File sections, slider syntax, sample-rate variable, stereo samples, namespaced function state | Language/API reference; original JSFX implementation |
| Cockos JSFX basic code reference: https://www.reaper.fm/sdk/js/basiccode.php | EEL2 functions, math operations, comparisons and conditional syntax | Language reference; no example DSP copied |
| Hyperbolic tangent identity: https://dlmf.nist.gov/4.28 | tanh in terms of exponentials, rewritten with nonpositive exponent | Established mathematical identity; original expression and code |
| One-pole exponential smoothing / first-order step response | `alpha=1-exp(-1/(tau*Fs))` | Standard mathematical technique; independently implemented |

These URLs identify algorithm and API provenance; this register does not claim
that pages were retrieved or that code was copied from them during development.
Boston, Tom Scholz, and Rockman are tonal references only; no endorsement or
exact circuit recreation is claimed. No assets are bundled.

No project-wide redistribution license is selected by this change. The repository
owner should choose one explicitly; citing mathematical references does not
license this project's source under a third-party implementation's license.

## v0.2 additions

The optional constant-peak band-pass uses the RBJ mathematical reference above;
its coefficient expressions are independently written. Cascaded tanh,
interstage RBJ filtering, and partial sqrt(gain) level compensation are original
project combinations of established techniques. No implementation code or audio
assets were imported. Flextron is an external comparison effect only: it is not
bundled, called, reverse engineered, or required by Bostone. The offline model
uses only Python's standard library. v0.1 production source remains unchanged.

## Plexi v0.3

See [Plexi research register](plexi-v0.3-references.md) for the required Marshall
schematic, both supplied circuit analyses, official EEL2 docs, selected values,
source-access limitations and explicit substitutions. Unlike the initial v0.1
register, these references were retrieved and reviewed during development.
The passive nodal/companion solver, biased preamp, differential power curves and
independent numerical/AC tests are original implementations of mathematical
techniques. No code, models, images, IRs or recordings are copied from the sites.

## Plexi v0.4 cabinet engine

See [v0.4 research and technical notes](plexi-v0.4-technical.md) for the official
JSFX I/O, serialization, strings, FFT/memory/PDC references and Cockos ReaVerb
guide reviewed before implementation. Partitioned overlap-add, linked
peak scaling, FIR resampling-area correction and the test FFT/SRC are original
implementations of established mathematics. No third-party convolution engine,
WAV asset, IR, recording, GPL/LGPL code, or proprietary ReaVerb implementation
is copied. Exact undocumented ReaVerb processing is not claimed.

The continuous-audio correction uses the documented native convolve_c primitive
inside an original bounded uniform packed-real FFT schedule. Official REAPER 7.47 Linux was
used as an external test host; neither its binary nor WDL source is bundled.
The optional runner adds test-only counter/guard output channels, not product
features or amplifier modifications.

The supplied reference archive was reviewed without importing source or IRs.
[File identities, licensing boundaries, convolution observations and future amp
recommendations](plexi-v0.4-reference-review.md) are recorded separately. Native
FFT scaling/final-bin behavior was validated against REAPER output, not copied
from the reference implementations.
