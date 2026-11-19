# Bostone Plexi v0.4 — cabinet IR operation

**Status update (2026-11-19):** The user confirms v0.4 continuous playback and successful cabinet switching in Windows REAPER. Earlier pending statements below describe the historical test stages; no new listening or runtime test is claimed by this path-only reorganization.

A separately installable amplifier plus cabinet loader. The v0.3 amp functions,
original ten sliders/defaults, initialization math and sample processing are
unchanged. Cabinet processing is appended AFTER the amp's output and its own
bypass. v0.3 and both existing preamps are untouched. There is no new amplifier
model, skin, hum cancellation, waveform display, cabinet asset or IR bundled.

## Installation and selecting an external WAV

1. In REAPER 7.x on Windows 11 choose **Options → Show REAPER resource path in
   explorer/finder**. Copy `plugins/Plexi/jsfx/Bostone_Plexi_v0.4.jsfx` into `Effects/Bostone`.
   Do not rename/overwrite `Bostone_Plexi_v0.3.jsfx` or any preamp file.
2. Create `Data/BostoneIR` in the same resource directory and copy your external
   WAVs into it. Typical normal-install location:
   `%APPDATA%\REAPER\Data\BostoneIR`. This is the IR directory, NOT Effects.
   Put mono/stereo 44.1 or 48 kHz WAVs directly in this folder; no subfolder
   browsing is implemented. Keep a stable unique filename for each IR.
3. Refresh the FX browser with **FX → Scan for new plugins** and insert
   **JS: Bostone Plexi v0.4**. Select the WAV using the native **IR WAV** dropdown.
   If newly copied files are absent, remove/reinsert v0.4 in a temporary project
   after saving settings, or restart REAPER. Do not append `.txt` to the JSFX.
4. Stop transport and lower/mute monitoring while loading. The status area shows
   the stored filename, successful frame/channel count, or a clear failure.
   File/normalization/length changes during playback queue until stopped and
   faded to cabinet bypass. The amp continues through the aligned dry path.
5. Click the status area's **[Reload]** line after repairing a missing/replaced
   file, or toggle a processing-mode/length setting. Reloading is synchronous;
   do not expect gap-free IR changes during live monitoring, even when stopped.

JSFX's documented native file selector scans a REAPER Data subfolder; this is
not ReaVerb's arbitrary-folder Browse dialog. There is no unsupported native
file-dialog call or assumed ReaScript-only API. The filename is explicitly
serialized as a string, rather than relying solely on the menu's numeric index.
Reopening a project reloads that external filename; the IR audio is not embedded
in the project. Folder reorder must not select a different impulse. The status
filename is authoritative if the menu list/order has changed. Keep IR files
available at the same Data-relative path on another machine; repair the menu
selection and Reload if moved. Verify this persistence workflow in REAPER.

## Cabinet controls (original amp sliders 1–10 unchanged)

| Index | Control | Range / default |
| --- | --- | --- |
| 11 | Cabinet Enable | Enabled; Bypass returns aligned amp output at unity |
| 12 | IR Level | -36 to +12 dB; default 0 dB; wet path only |
| 13 | IR Processing | Normal Raw (default), Apply -18 dB, Peak Normalize 0 dBFS, Peak Normalize -18 dBFS |
| 14 | Cabinet Wet | -120 to +6 dB; default 0 dB; -120 means exact mute |
| 15 | Cabinet Dry | -120 to +6 dB; default -120 (muted) |
| 16 | Cabinet Highpass | 0–2000 Hz; default 0 (off) |
| 17 | Cabinet Lowpass | 0–20000 Hz; default 0 (off) |
| 18 | IR Maximum Length | 0–500 ms; default 0 = full file, subject to capacity |
| 19 | IR WAV | Filename selector in Data/BostoneIR |

Dry means the amp's output before cabinet convolution, not the guitar DI.
**Amp Enable bypasses only the original amplifier**; the cabinet can still
process that signal. Cabinet Enable is its separate bypass. For an amp-only
comparison disable Cabinet, leaving Amp Enable as desired. Fully settled cabinet
bypass ignores IR level, filters, normalization and wet/dry settings: it returns
the original amp output at unity, delayed by exactly 64 samples. Linux batch PDC/bypass behavior is tested; Windows real-time host bypass still
needs verification.

Normal Raw introduces no peak normalization, silence trimming, onset alignment,
phase conversion, automatic output compensation or safety limiter. Leading
silence, stereo balance and coefficient gain are retained. Original WAV rates
are converted to the actual FX processing rate when needed, with FIR-area gain
correction. Normalization is linked across both channels; see the technical
notes for exact equations. Filters and gain controls affect wet only.

Explicit length adjustment keeps the FIRST requested number of frames, including
leading silence, and hard-crops the tail without stretching, fading or recentering.
This can change frequency response; leave 0 for the original file. Nothing is
silently cropped to fit memory.

## Supported size, rate and safety behavior

- WAV input rates: 44.1/48 kHz, one or two channels. Decoding and resampling use
  REAPER's native media API. PCM/float codec variants still need host tests.
- Maximum **4096 frames after resampling/cropping**: about 92.9 ms at 44.1 kHz,
  85.3 ms at 48 kHz, 42.7 ms at 96 kHz, or 21.3 ms at 192 kHz. The selected length
  is checked against this capacity. Oversized files are rejected with a message.
- Mono IR is used on both independent inputs. Stereo means L input*IR L and
  R input*IR R; there is no crossfeed, sum-to-mono or four-channel true stereo.
- Missing, wrong-format, empty, truncated, non-finite or transform-overflow files
  fail to aligned amp-only bypass. A valid all-zero IR is deliberately silent
  on the wet path. Repair the file/selection and Reload; failure is not a limiter.
- File reads/transforms occur only in initialization or queued stopped-transport
  preparation, not per-sample processing. Filesystem I/O can still stall the
  audio thread; mute monitoring before loading. Initial project/rate/transport
  reinitialization may prepare the saved IR before the first audio block.
- Sample-rate changes clear convolution history and reload the saved file at the
  new effective rate. Do not change device rates mid-performance. No old-rate
  coefficients or stale IR tails are retained.

The amp's original wet ceiling still applies BEFORE the cabinet. A faithful IR
can amplify beyond 0 dBFS; no extra limiter or automatic attenuation is added.
Start IR Level low when auditioning unfamiliar files. Non-finite/extreme output
faults disengage the cabinet to the aligned amp path and display an error.

For very long IRs, heavy whole-FX oversampling, arbitrary-folder browsing, or
uninterrupted hot swapping, use v0.3 plus ReaVerb instead of stretching this
bounded first JSFX implementation. This is a cabinet engine, not a general
long-reverb replacement. Host oversampling affects both amp and cabinet in v0.4;
CPU and IR-frame requirements rise accordingly. To oversample only the amp,
use separate v0.3 → ReaVerb.

See [engine and ReaVerb mapping](plexi-v0.4-technical.md) and
[automated/manual validation](plexi-v0.4-testing.md).

For a longer WAV at 44.1/48 kHz, explicitly set Maximum Length to **80 ms**
and confirm Loaded status. At oversampled rates use a shorter crop or external
ReaVerb. The default 0 remains full-file: oversized files fail to amp-only output,
never silently shorten. Cropping can change cabinet tone. The user's cabinet-off
plus external ReaVerb chain is the working baseline for Windows retesting.
