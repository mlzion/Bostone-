# Bostone Preamp

An independently installable stereo guitar preamp/EQ and soft-clipping prototype
for REAPER 7.x, useful before Plexi or another amplifier.

- **v0.1**: initial pre-EQ → drive → post-EQ foundation.
- **v0.2**: alternate band-pass mode and cascaded drive stages.
- **v0.2.1**: expanded low-cut/low-mid ranges and revised high-cut maximum,
  preserving v0.2's remaining processing and defaults.

Copy any desired files from [jsfx](jsfx/) into **Effects/Bostone/** in REAPER's
resource directory; keep their filenames. Refresh **FX → Scan for new plugins**.
Display names, controls, defaults and saved project identities are unchanged.
Existing installations need no migration. REAPER requires no repository folder
structure, Python or external runtime code.

- [v0.1/v0.2 overview and installation](docs/v0.1-v0.2-guide.md)
- [Signal chain](docs/signal-chain.md), [DSP notes](docs/dsp-notes.md), [filter response](docs/filter-response.md)
- [Test plan](docs/testing.md) and [v0.2.1 usage/testing](docs/preamp-v0.2.1.md)
- [Algorithm/licensing register](../../shared/source-register.md)

From the repository root: `python3 run_tests.py --plugin Preamp`.
These remain experimental prototypes; historical test reports distinguish
numerical checks from host/listening validation. No preamp processing is changed
by the repository reorganization.
