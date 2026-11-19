# Bostone audio plugins

Bostone is a family of independently installable REAPER JSFX guitar processors.
Each plugin has its own source, documentation and tests. These are experimental
DSP models, not claims of exact circuit emulation or endorsement by referenced
artists or manufacturers. No cabinet IRs or recordings are bundled.

| Project | Available versions | Purpose and status |
| --- | --- | --- |
| [Preamp](plugins/Preamp/README.md) | v0.1, v0.2, v0.2.1 | Guitar pre-EQ and cascaded soft clipping; v0.2.1 expands pre-EQ frequency ranges |
| [Plexi](plugins/Plexi/README.md) | v0.3, v0.4 | Circuit-inspired amplifier; v0.4 adds a bounded cabinet IR loader, confirmed working by the user in Windows REAPER |

## Repository layout

```text
plugins/
  Plexi/{jsfx,docs,tests}/
  Preamp/{jsfx,docs,tests}/
shared/
  source-register.md
  tests/test_jsfx_compatibility.py
run_tests.py
README.md
CHANGELOG.md
```

`shared/` contains the existing cross-project algorithm/licensing register and
source-compatibility checks. It contains no runtime DSP dependencies. Future
plugins can have their own project directory; none are introduced here.

## Install in REAPER on Windows 11

1. Choose **Options → Show REAPER resource path in explorer/finder**.
2. Copy the desired `.jsfx` files from `plugins/Preamp/jsfx/` or
   `plugins/Plexi/jsfx/` into the resource directory's **Effects/Bostone/** folder
   (typically `%APPDATA%\REAPER\Effects\Bostone`). Keep filenames unchanged.
3. Refresh the FX browser using **FX → Scan for new plugins** and select the
   existing JSFX display name. Reopen the browser or restart REAPER if necessary.

The GitHub paths changed; the REAPER installation destination did not. Existing
installations and project plugin identities need no migration. REAPER does not
need the repository folders, Python, or shared files at runtime. Do not add a
second installed copy under a different path. All historical versions remain
separately available.

Plexi v0.4 external WAVs still go in **Data/BostoneIR/** under the REAPER resource
path. Its saved filenames, loading, controls and 4096-processed-frame capacity
are unchanged. See [cabinet installation/usage](plugins/Plexi/docs/plexi-v0.4-cabinet.md).

## Development and tests

From the repository root with Python 3.9+ (standard library only):

```console
python3 run_tests.py
python3 run_tests.py --plugin Plexi
python3 run_tests.py --plugin Preamp
```

The runner uses separate discovery processes for each project, then runs the
existing shared compatibility suite. Individual project commands include those
shared checks, which scan all installed source files in this repository.
Direct discovery is also supported with `python3 -m unittest discover -s
plugins/Plexi/tests -v` or `plugins/Preamp/tests` (one line per command).
Cross-project historical source-identity assertions remain in the tests.

Optional actual REAPER host tests:

```console
python3 plugins/Plexi/tests/run_reaper_cabinet.py --reaper /path/to/reaper --seconds 30 --report /tmp/report.json
```

Numerical/source tests are not a substitute for REAPER compilation or listening.
Prior native Linux results and the user's Windows confirmation are documented
in the Plexi project. This reorganization changes paths/documentation only;
all five production JSFX files retain their original bytes.

See [history](CHANGELOG.md), [source and licensing register](shared/source-register.md),
and each project's documentation. No project-wide redistribution license has
been selected; reference licenses do not relicense independently written code.
