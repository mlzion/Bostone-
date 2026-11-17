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
