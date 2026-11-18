# Plexi v0.3 research and source register

Research performed before DSP implementation on 2026-11-17. All production and
test code is original. No simulator source, SPICE model, JSFX, IR, recordings,
third-party waveshaper or GPL/LGPL implementation was copied or imported.
The cited web simulators are reference material, not dependencies or licensed
component models for this product. Historical circuits are distinguished from
those sites' proprietary implementations.

## Required references reviewed

1. [Marshall 1959 schematic PDF](https://schematicheaven.net/marshallamps/jmp_superlead_100w_1959.pdf).
   Retrieved through web research; three-page scan, with screenshot requests and
   indexed drawing description. It establishes the multistage preamp → tone
   network → inverter → output-bank ordering. The scan has limited legibility
   in the available extraction: it cannot verify every small value or establish
   one exact 1968 specification. No voltage, transformer or supply constants
   are claimed from unreadable markings. This prototype is not a complete
   transcription of the PDF. No schematic image is redistributed.
2. [1968-style preamp reference](https://bench.swellamps.com/preamp-2ch-1968/).
   The part list identifies a bright ECC83/12AX7 stage with 100 kΩ plate load,
   2.7 kΩ cathode resistor, 680 nF bypass, 2.2 nF coupling and 1 MΩ volume;
   the latter pair gives a simple unloaded RC corner about 72 Hz. It also
   describes a later gain stage, follower, tone stack, inverter and EL34 bank.
   The first-stage tilt (190 Hz) and coupling range (70–300 Hz) are inspired by
   these values; they are substituted one-pole/tilt blocks, not loaded circuit
   solutions. Normal-channel mixing, volume bright-cap interaction and actual
   cathode-follower nonlinearity are omitted. The page describes representative
   variants, not proof that all late-1960s amplifiers have the same parts.
3. [Marshall tone-stack analysis](https://bench.swellamps.com/filters/marshall-1959/).
   Selected values verified against its parts list: 33 kΩ slope, 500 pF treble,
   two 22 nF caps, 220 kΩ Treble, 1 MΩ Bass, 25 kΩ split Middle, and 2 MΩ load.
   The site describes the bass return through the middle track and the mid cap
   at its wiper. v0.3 derives nodal equations independently for that topology.
   220 kΩ Treble is the selected analysis variant; 250 kΩ variants exist and
   are NOT silently treated as identical. No claim that 220 kΩ is a universal
   1968 value is made. Source impedance is simplified to zero; its 60 pF load
   capacitance is omitted. This changes HF response from a fully loaded circuit.
4. [Official JSFX structure](https://www.reaper.fm/sdk/js/js.php),
   [EEL2 math/operators](https://www.reaper.fm/sdk/js/basiccode.php), and
   [function namespaces](https://www.reaper.fm/sdk/js/userfunc.php).
   Reviewed sections, slider enums, local/instance scope, ternary blocks,
   loops, memory addressing, srate and initialization. The math reference
   documents pow(x,y), exp(), log(), min/max and exact === comparisons. This
   source uses exp(log(10)*dB/20), no pow() calls or caret operators, and decimal
   literals only. Static syntax policy is conservative, not a replacement for
   REAPER's actual compiler.

## Additional verification

[Official REAPER user guide](https://dlx.reaper.fm/userguide/html/) documents the
FX-instance oversampling context menu and target-rate options. The manual used
for research is newer than the target 7.47 installation; the host checklist
requires verifying the actual menu labels and effective rates there.

## Explicit design assumptions, not verified circuit specifications

Bias offsets 0.22/0.1/0.04, PI gain/imbalance, stage gains, fixed recovery gain 3,
softplus/rational conduction, fixed 10/150 ms rail memory and 0.18 sag strength,
1.2 kHz Presence shelf, 35 Hz input/10 Hz DC/18 kHz input/10 kHz output filters,
and ±0.8 safety saturation are normalized digital voicing choices. None are
claimed EL34 device parameters, measured transformer response, exact feedback
values, or historical power-supply specifications. Bass uses an assumed square
control taper; resistance floors prevent pot endpoint singularities.

The model is inspired by 1959 signal-flow and frequency-selective gain. Audible
similarity, power-stage feel and comparisons against Flextron remain unverified.
No project-wide redistribution license is selected here; original repository
licensing status is unchanged. No endorsement by Marshall or other makers is claimed.
