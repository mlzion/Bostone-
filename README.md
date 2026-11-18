# Bostone v0.2 — JSFX filtering and drive experiments

An original stereo preamp experiment inspired by Boston / Tom Scholz guitar tones.
This is an exploratory signal chain, not an exact Rockman circuit model.
Target: REAPER 7.x on Windows 11. No VST3, C++, or JUCE development is included.

Input Gain → Pre-EQ → Drive / tanh soft clipping → Post-EQ → Output Gain.
Each stage has its own enable switch; Master Bypass returns the dry stereo input
following a 10 ms crossfade. The interface uses REAPER's standard JSFX sliders.

## v0.2 and the v0.1 baseline

v0.2 ships as **Bostone_Preamp_v0.2.jsfx**, displayed as **Bostone Preamp v0.2**.
The original **Bostone_Preamp.jsfx** remains byte-for-byte unchanged, displayed as
**Bostone v0.1 - Preamp Prototype**. Existing projects keep their original FX.
No shared imports or external assets are needed. New version files will follow
`Bostone_Preamp_vX.Y.jsfx`; the historical v0.1 file keeps its existing name.

v0.2 extends Pre High Cut to 400 Hz, adds an optional band-pass alternative and
an optional two-stage drive. **Both mode selectors default to Legacy**; all
original slider indices/defaults are retained. Compressor/sustainer work is
explicitly deferred until filter/drive host testing establishes a stable base.

## Install in REAPER on Windows 11

1. In REAPER, choose **Options → Show REAPER resource path in explorer/finder**.
   This is the authoritative location, including for portable installations.
   A typical normal installation uses `%APPDATA%\REAPER`.
2. Create `Effects\Bostone` inside that resource directory.
3. Copy both [Bostone_Preamp.jsfx](jsfx/Bostone_Preamp.jsfx) and
   [Bostone_Preamp_v0.2.jsfx](jsfx/Bostone_Preamp_v0.2.jsfx) into that folder:
   `%APPDATA%\REAPER\Effects\Bostone\` for a typical normal installation.
   Do not rename or overwrite v0.1 with v0.2. Ensure Windows has not appended
   `.txt` to either filename. No Python or other files are needed.
4. Open a track's FX browser and choose **FX → Scan for new plugins** to refresh
   the list. Search for `Bostone`; select **JS: Bostone v0.1 - Preamp Prototype**.
   v0.2 appears separately as **JS: Bostone Preamp v0.2**. Both names must be
   present. If either is missing, close/reopen the browser or restart REAPER.
   For later v0.2 updates, replace only `Bostone_Preamp_v0.2.jsfx`, then remove
   and re-add that FX in a temporary test project (save instance settings first).
5. Start with a low monitor level. The default output is -6 dB, but large input
   and EQ boosts can still exceed 0 dBFS. No final limiter is included.

The JSFX **Edit** window should show no compilation error. See
[manual testing](docs/testing.md) before treating the prototype as validated.

## Original controls (indices 1–17 retained)

| Section | Control | Range | Default |
| --- | --- | --- | --- |
| Input | Gain | -24 to +24 dB | 0 dB |
| Input | Enable | Off / On | On |
| Pre-EQ | Low Cut | 40–300 Hz | 80 Hz |
| Pre-EQ | Low-Mid Gain | -12 to +12 dB | 0 dB |
| Pre-EQ | Low-Mid Frequency | 150–1000 Hz | 400 Hz |
| Pre-EQ | High Cut | v0.1: 2000–15000 Hz; v0.2: 400–15000 Hz | 10000 Hz |
| Pre-EQ | Enable | Off / On | On |
| Distortion | Drive | 1–20 | 3 |
| Distortion | Enable | Off / On | On |
| Post-EQ | Low Gain | -12 to +12 dB | 0 dB |
| Post-EQ | Mid Gain | -12 to +12 dB | 0 dB |
| Post-EQ | Mid Frequency | 400–4000 Hz | 1200 Hz |
| Post-EQ | High Gain | -12 to +12 dB | 0 dB |
| Post-EQ | Enable | Off / On | On |
| Output | Gain | -24 to +12 dB | -6 dB |
| Output | Enable | Off / On | On |
| Global | Master Bypass | Off / On | Off |

The added Input and Output Enable controls make gain stages independently
bypassable. Drive 1 still applies tanh; use Distortion Enable to remove it.

## Added v0.2 controls

| Index | Control | Range | Default |
| --- | --- | --- | --- |
| 18 | Pre-EQ Mode | Legacy HP Bell LP / Band-pass | Legacy |
| 19 | Band-pass Center | 150–4000 Hz | 685 Hz |
| 20 | Band-pass Q | 0.25–4 | 1 |
| 21 | Band-pass Level | -12 to +12 dB | 0 dB |
| 22 | Drive Mode | Legacy Tanh / Cascaded | Legacy |
| 23 | Cascade Stage Gain | 0–18 dB | 12 dB |
| 24 | Cascade Interstage Cut | 800–12000 Hz | 6000 Hz |
| 25 | Cascade Level Trim | -12 to +12 dB | 0 dB |

In band-pass mode, Low Cut/Low-Mid/High Cut controls remain stored but only affect
Legacy pre-EQ. Band-pass Level controls center gain separately from Q. In Legacy
drive mode, cascade controls have no effect. Existing Pre-EQ and Distortion
Enable switches bypass either selected mode. Mode changes crossfade for 10 ms.

For a v0.1 comparison, insert both FX on the same track, transfer the original
17 values manually, and enable only one FX at a time using REAPER's FX bypass
checkboxes. Do not run both active in series for this comparison. Keep selectors
18 and 22 on Legacy. Existing v0.1 presets/projects remain attached to v0.1;
there is no automatic preset migration between distinct JSFX identities.
See [the full A/B procedure](docs/testing.md#v02-acceptance-and-ab-plan).

## Offline checks

With Python 3.9 or newer, from the repository root:

```console
python -m unittest discover -s tests -v
```

Only the Python standard library is required. This is a separate numerical
reference model, not an EEL2 interpreter or REAPER host. It cannot establish
JSFX compilation, automation integration, audible quality, or CPU performance.
The same command also runs conservative compatibility checks on the actual JSFX
source. See [syntax corrections and runtime status](CHANGELOG.md).

See [signal chain](docs/signal-chain.md), [DSP notes](docs/dsp-notes.md),
[source register](docs/source-register.md), and [test procedure](docs/testing.md).

## Bostone Plexi v0.3 — standalone amplifier prototype

Plexi is a separately installable experiment inspired by a cranked Marshall
1959 Super Lead, not a claim of exact circuit or EL34 emulation. The existing
v0.1 and v0.2 files remain unchanged; all three FX can be installed together.

Copy [Bostone_Plexi_v0.3.jsfx](jsfx/Bostone_Plexi_v0.3.jsfx) alongside the other
JSFX in the REAPER resource-path `Effects/Bostone` folder. Refresh the FX browser
with **FX → Scan for new plugins** and select **JS: Bostone Plexi v0.3**. Do not
rename or overwrite the older files. No runtime dependencies or cabinet IRs
are included.

Input conditioning → bright asymmetric preamp → adjustable interstage bass
filter → second preamp → interactive passive RC tone stack → phase inverter
→ push-pull power-stage approximation → Presence/output filtering → level.
Start with clean DI and defaults (Preamp 6 dB, Power 3 dB, Output -12 dB), at a
low monitor volume. When driven by v0.2, begin with Input -12 dB / Output -18 dB.

- [Installation, all ten controls, 2x/4x host oversampling and A/B checklist](docs/plexi-v0.3-testing.md)
- [DSP architecture, tone-stack netlist, dynamics and limitations](docs/plexi-v0.3-dsp.md)
- [Reviewed sources, verified selected values and explicit substitutions](docs/plexi-v0.3-references.md)

Intended chain: **Bostone v0.2 → Plexi → ReaVerb (your Marshall 1960 IR)**.
Compare with **v0.2 → Flextron (cab disabled) → ReaVerb (same IR)** at matched
perceived loudness. No custom oversampling, reverb, widening or cabinet model
is in Plexi. REAPER compilation/listening/CPU/actual host oversampling tests
remain pending; automated numerical checks do not establish host compatibility.
Do not merge the Plexi PR automatically.

## Bostone Preamp v0.2.1 — expanded pre-EQ range

Install [Bostone_Preamp_v0.2.1.jsfx](jsfx/Bostone_Preamp_v0.2.1.jsfx) alongside
older files; the FX browser displays **Bostone Preamp v0.2.1**. v0.1, v0.2 and
Plexi v0.3 are unchanged. Defaults and all other processing remain as in v0.2.

| Control | v0.2.1 range | Default |
| --- | --- | --- |
| Pre Low Cut | 40–1000 Hz | 80 Hz |
| Pre Low-Mid Frequency | 150–2000 Hz | 400 Hz |
| Pre High Cut | 400–10000 Hz | 10000 Hz |

Use **Legacy** Pre-EQ Mode with Pre-EQ enabled to try an 800 Hz high-pass before
Plexi; these three controls remain inactive in the alternative Band-pass mode.
See [installation, compatibility notes and test plan](docs/preamp-v0.2.1.md).
Actual REAPER compilation/listening and click checks remain pending.
