# Bostone Plexi v0.3 DSP architecture

An original circuit-inspired experiment, not a component-accurate Marshall model.
There is no cabinet, convolution, stereo crossfeed or effect bus. v0.1 and
v0.2 are preserved unchanged. This branch includes the latest main with v0.2
merged; Plexi remains independently installable and does not require either
preamp to be loaded.

## Processing order

1. Input gain, 35 Hz DC/rumble HP, 18 kHz one-pole LP (rate-clamped).
2. Bright-channel-inspired tilt: x + 0.9*(x - LP190(x)), then biased tanh stage.
3. Bass Tightness HP, 70–300 Hz, ahead of all subsequent nonlinear stages.
4. A hot rational preamp curve with a different bias; 10 Hz DC removal.
5. Interactive passive B/M/T RC network solved with capacitor companions.
6. Fixed gain 3 after insertion loss, then unequal soft phase-inverter branches.
7. Two soft conduction branches with bounded current, differential recombination,
   and independent load-envelope/rail memory per channel.
8. 10 Hz DC removal, Presence HF-feedback surrogate, two 10 kHz one-pole LPs.
9. Explicit 0.8-amplitude safety saturator, then nonpositive Output Level.

All fixed pole frequencies are clamped to 0.45*srate. LP updates use
`a=1-exp(-2*pi*f/Fs)`, `state += a*(x-state)`; HP is x-LP(x). These first-order
filters have gradual minimum-phase responses; Bass Tightness is not a brick-wall
cut. Bass changes BEFORE later distortion rather than trying to remove already
created low-frequency intermodulation at the output. Phase shift around the
cutoff is unavoidable, bounded, and should be auditioned at both endpoints.

## Nonlinear stages

The exp-based tanh identity never evaluates an exponential of a positive large
number. Biased stages subtract their exact zero-input output:

- Stage 1: tanh(0.8*PreampGain*x + 0.22) - tanh(0.22).
- Stage 2: r(3*x+0.1) - r(0.1), where r(x)=x/(1+abs(x)). This is smooth through
  the knee with a continuous first derivative, but is not an analytic tube law.
- PI: pA=tanh(2*x+0.04)-tanh(0.04),
  pB=tanh(-1.9*x+0.04)-tanh(0.04). The slight imbalance is an explicit voicing
  choice, not a claimed translation of particular plate resistor values.
- Power branches: softplus(u)=max(0,u)+log(1+exp(-abs(u))),
  current(u)=softplus(u)/(1+softplus(u)); differential output is
  2*rail*[current(3*(PowerGain*pA-0.1))-current(3*(PowerGain*pB-0.1))].

The power curve supplies smooth conduction onset and a finite-current ceiling,
with push-pull cancellation at silence. It is inspired by grid threshold and
plate-current saturation; it is NOT an EL34 physical current law, load-line
solution or output compressor relabeled as a tube model. No grid-current,
screen-current, transformer hysteresis, speaker impedance, blocking distortion,
reactive negative-feedback loop or exact valve bias voltages are modeled.

A fixed modest rail surrogate follows mean branch magnitude, with 10 ms attack
and 150 ms release; rail=1/(1+0.18*envelope). It reduces available output swing
under load, independently per channel. These are chosen prototype constants,
not measured supply or rectifier specifications. No user compressor/sag controls
are added. A real amp has a shared supply; independent rails here preserve stereo
isolation. PI imbalance plus asymmetric preamp can create even harmonics; the
coupling and output DC filters control resulting offsets. There is no hum model.

Presence adds 0–1.2 times the signal's 1.2 kHz high-pass component AFTER the power
stage. This stable feed-forward shelf approximates the high-frequency effect of
reduced negative feedback; it is not a solved feedback circuit. Final filtering
is gentle amplifier bandwidth shaping, NOT a cabinet response.

## Interactive tone stack: original nodal implementation

Selected reference values and variants are recorded in
[plexi-v0.3-references.md](plexi-v0.3-references.md). The circuit is a passive
network, not independent EQ bands. The following netlist fully defines it:

| Element | Connection | Selected value |
| --- | --- | --- |
| Slope | input → S | 33 kΩ |
| Treble cap | input → T | 500 pF |
| Bass cap | S → B | 22 nF |
| Mid cap | S → W | 22 nF |
| Treble upper | T → O | max(100 Ω, 220 kΩ*(1-t)) |
| Treble lower | O → B | max(100 Ω, 220 kΩ*t) |
| Bass + upper mid | B → W | max(100 Ω, 1 MΩ*b*b) + max(25 Ω, 25 kΩ*(1-m)) |
| Lower mid | W → ground | max(25 Ω, 25 kΩ*m) |
| Load | O → ground | 2 MΩ |

b,m,t range from 0 to 1. The Bass pot plus upper middle track are series-only
and their intermediate node is algebraically eliminated. Middle is a split pot:
bass returns through its upper part, the mid capacitor lands at its wiper W.
Changing a knob therefore changes the loading seen by the others. The source
is an ideal voltage source, substituting for a low-impedance cathode follower.
The chosen square Bass taper, resistance floors, ideal source and purely
resistive PI load are explicit approximations, not historical part claims.

For each capacitor the trapezoidal companion conductance is G=2*Fs*C and current
is G*(va-vb)+h. After the nodal solve, h becomes -2*G*(va-vb)-h. Treble history is
oriented from T to input; bass/mid histories from S toward B/W. Five simultaneous
node equations are solved by a shared inverse. Left and right have distinct
capacitor histories. The conductance matrix is symmetric positive definite with
positive resistances and a grounded load. The code floors pivots defensively;
normal tested settings never require that floor. This passivity argument applies
to a fixed network; rapid pot automation still requires listening tests.

The inverse is rebuilt at most every 16 samples while smoothed B/M/T positions
change, and reused when settled. This bounds CPU; controls are first smoothed
with a 20 ms time constant. Conductance steps can produce small transients and
must be tested in REAPER. Other gain/pole controls use the same 20 ms smoother;
Enable has an exact-endpoint 10 ms linear ramp. No allocation occurs per sample.

## Integrity, levels and rates

Each channel's complete nonlinear and filter history is namespaced separately.
Wet processing continues while bypassed. With Enable fully off the original
finite dry input is returned exactly; malformed NaN/infinite host samples become
zero. During the 10 ms transition dry/wet signals blend, so dry signals above
the wet ceiling can exceed that ceiling. The active path clamps pathological
input to ±16 before gain, detects non-finite output/large capacitor history,
resets only the affected channel on faults, and flushes tiny histories below
0.000000000000000000000000000001. Fault reset is containment, not transparent
recovery. Final wet output magnitude is at most 0.8 at Output 0 dB, and at most
0.8*10^(OutputDB/20) otherwise. This saturator is a safety voicing element that
can itself add distortion, not a brick-wall intersample/true-peak guarantee.

Normal JSFX @init reinitialization is retained for sample-rate changes and
transport starts. All states reset and targets snap on initialization; no
ext_noinit override, serialized audio history, latency or custom resampler is
used. REAPER should supply the actual FX processing rate through srate when host
oversampling is active. Tests cover equivalent higher model rates, NOT the host
resampler or its bypass latency. Nonlinear aliasing is expected at 1x; host 2x/4x
may reduce it but cannot make this model alias-free.

CPU is intended to be modest, with fixed small matrix work during tone automation
and more math in the nonlinear stages than v0.1. REAPER CPU and listening quality
are unmeasured. See [host checklist](plexi-v0.3-testing.md).
