# Bostone Plexi

An experimental stereo, circuit-inspired guitar amplifier for REAPER 7.x.
This project is independently installable; Preamp is an optional upstream effect.

- **v0.3**: standalone amplifier, designed for an external cabinet such as ReaVerb.
- **v0.4**: the same amplifier with a WAV cabinet IR loader. The user confirmed
  continuous playback and successful cabinet switching on Windows REAPER.

Copy either or both files from this project's [jsfx](jsfx/) directory into
**Effects/Bostone/** under REAPER's resource path. Keep filenames and existing
installation paths unchanged. Refresh **FX → Scan for new plugins**. The display
names remain **Bostone Plexi v0.3** and **Bostone Plexi v0.4**. No repository
folders or external runtime code are required.

For v0.4, put your own IR WAVs in **Data/BostoneIR/**. The 4096-processed-frame
limit is unchanged; at 44.1/48 kHz an explicit 80 ms crop fits. No IR is bundled.

- [v0.3 architecture](docs/plexi-v0.3-dsp.md) and [installation/tests](docs/plexi-v0.3-testing.md)
- [v0.4 cabinet usage](docs/plexi-v0.4-cabinet.md), [architecture](docs/plexi-v0.4-technical.md), [validation](docs/plexi-v0.4-testing.md)
- [Cabinet reference review and future amp recommendations](docs/plexi-v0.4-reference-review.md)
- [Research register](docs/plexi-v0.3-references.md) and [shared provenance](../../shared/source-register.md)

From the repository root: `python3 run_tests.py --plugin Plexi`.
Optional host runner: `python3 plugins/Plexi/tests/run_reaper_cabinet.py --reaper
/path/to/reaper --seconds 30 --report /tmp/report.json` (one line).
The model remains a prototype. No amplifier changes accompany this organization.
