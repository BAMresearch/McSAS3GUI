# McSAS3GUI (v0.2.1)

[![PyPI Package latest release](https://img.shields.io/pypi/v/mcsas3gui.svg)](https://pypi.org/project/mcsas3gui)
[![Commits since latest release](https://img.shields.io/github/commits-since/BAMresearch/mcsas3gui/v0.2.1.svg)](https://github.com/BAMresearch/mcsas3gui/compare/v0.2.1...main)
[![License](https://img.shields.io/pypi/l/mcsas3gui.svg)](https://en.wikipedia.org/wiki/MIT_license)
[![Supported versions](https://img.shields.io/pypi/pyversions/mcsas3gui.svg)](https://pypi.org/project/mcsas3gui)
[![PyPI Wheel](https://img.shields.io/pypi/wheel/mcsas3gui.svg)](https://pypi.org/project/mcsas3gui#files)
[![Weekly PyPI downloads](https://img.shields.io/pypi/dw/mcsas3gui.svg)](https://pypi.org/project/mcsas3gui/)
[![Continuous Integration and Deployment Status](https://github.com/BAMresearch/mcsas3gui/actions/workflows/ci-cd.yml/badge.svg)](https://github.com/BAMresearch/mcsas3gui/actions/workflows/ci-cd.yml)
[![Coverage report](https://img.shields.io/endpoint?url=https://BAMresearch.github.io/mcsas3gui/coverage-report/cov.json)](https://BAMresearch.github.io/mcsas3gui/coverage-report/)

McSAS3GUI is the desktop application for McSAS3. It guides you through loading
SAXS/SANS data, previewing a model fit, running the Monte Carlo optimization,
and turning the result into histograms.

If you are unfamiliar with Python environments, start with one of the two paths
below. The rest of this README is mostly for people who want to script,
customize, or build McSAS3GUI themselves.

## Start Here

### Option 1: Download the application

For prebuilt standalone binaries, see the latest GitHub release:

- https://github.com/BAMresearch/mcsas3gui/releases/latest

Release assets are built for tagged releases. This is the easiest path when a
release is available for your operating system.

### Option 2: Run with one `uv` command

If [`uv`](https://docs.astral.sh/uv/) is installed, run:

```bash
uvx --python 3.14 --from mcsas3gui m3gui
```

The first run may take a few minutes. `uvx` creates an isolated Python
environment, installs McSAS3GUI and McSAS3, and then starts the `m3gui`
application. You do not need to create or activate a virtual environment.

If `uv` is not installed yet:

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

On Windows PowerShell:

```powershell
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
```

After installing `uv`, close and reopen the terminal if the `uvx` command is not
found.

### Keep the command installed

For regular use from the terminal, install the GUI command once:

```bash
uv tool install --python 3.14 mcsas3gui
m3gui
```

## First Run

1. Open the **Getting Started** tab.
2. Choose **Quick Start demo** from the template list.
3. Use the loaded example settings to preview the data and model.
4. Run the optimization.
5. Run histogramming to create the distribution plot.

The optimization produces an HDF5 result file. Histogramming adds distribution
results to that file and writes a PDF plot next to it.

## What the Tabs Do

- **Getting Started** loads complete example workflows.
- **Data Loading** tells McSAS3 how to read your data file.
- **Run Settings** sets the scattering model and optimization limits.
- **McSAS3 Optimization** runs one or more optimizations.
- **Histogram Settings** defines the distributions to calculate.
- **(Re-)Histogramming** recalculates histograms from existing optimization
  results, without rerunning the optimization.

Both optimization buttons are abortable. While running, they change to
`Running... Click to abort.` and forward a stop request to the core McSAS3
runner.

## Other Installation Options

McSAS3GUI requires Python 3.12 or newer. The examples in this README use
Python 3.14, the current recommended runtime.

Install the released GUI package with `pip`:

```bash
pip install mcsas3gui
```

If you prefer a manually managed `uv` environment:

```bash
uv venv --python 3.14
source .venv/bin/activate
uv pip install mcsas3gui
m3gui
```

On Windows, activate the environment with `.venv\Scripts\activate` instead of
`source`.

You can also install the in-development version with `pip`:

```bash
pip install git+https://github.com/BAMresearch/mcsas3gui.git@main
```

or, from a local source checkout with `uv`:

```bash
uv venv --python 3.14
source .venv/bin/activate
uv pip install ../McSAS3 .
mcsas3gui --version
```

Run the local source command from the `McSAS3GUI` repository with the `McSAS3`
repository checked out next to it.

After activating an environment, these launch commands all work:

```bash
mcsas3gui
m3gui
python -m mcsas3gui
```

## Standalone GUI bundles

A standalone build path is available for local packaging and CI:

```bash
tox -e standalone
```

This produces a platform-specific standalone bundle under `dist/standalone/`, including the
windowed `McSAS3GUI` app and the bundled `mcsas3-histogrammer` helper used by the histogramming
tabs.

Linux standalone release artifacts are built in a `manylinux_2_34` container so the produced
bundle stays compatible with systems that provide GLIBC 2.34 or newer. Local Linux builds need the
Qt xcb runtime packages listed in `ci/requirements_linux.txt`.

### Standalone release process

Standalone release assets are produced by the GitHub Actions workflow in
`.github/workflows/standalone-release.yml`.

The release workflow:

- checks out both `McSAS3GUI` and `McSAS3`
- runs `tox -e standalone` on Linux, macOS, and Windows, with Linux built from a GLIBC 2.34 baseline
- signs the macOS `.app` bundle with a Developer ID certificate
- notarizes and staples the macOS bundle with `notarytool` and `stapler`
- uploads the platform zip archives to the GitHub release

For local development builds, `tox -e standalone` produces the same bundle layout, but notarization
only happens in the release workflow because it requires GitHub secrets and Apple credentials.

### GitHub secrets for macOS standalone releases

The macOS release build requires these GitHub Actions secrets:

- `MACOS_CERT_P12_BASE64`
- `MACOS_CERT_P12_PASSWORD`
- `MACOS_CODESIGN_IDENTITY`
- `MACOS_KEYCHAIN_PASSWORD`
- `MACOS_NOTARY_KEY_ID`
- `MACOS_NOTARY_ISSUER_ID`
- `MACOS_NOTARY_API_KEY`

You can prepare all of them in one step with:

```bash
tools/prepare_github_secrets.sh \
    --p12-path ~/Downloads/mcsas3gui-signing-cert.p12 \
    --p12-password '<p12-password>' \
    --p8-path ~/Downloads/AuthKey_ABC123XYZ.p8 \
    --issuer-id 12345678-1234-1234-1234-123456789abc
```

The helper script:

- base64-encodes the `.p12` signing certificate as `MACOS_CERT_P12_BASE64`
- reuses the supplied `.p12` password as `MACOS_CERT_P12_PASSWORD`
- imports the `.p12` into a temporary macOS keychain to discover `MACOS_CODESIGN_IDENTITY`
- emits `MACOS_KEYCHAIN_PASSWORD` for the temporary runner keychain used in CI
- reads the raw `.p8` contents into `MACOS_NOTARY_API_KEY`
- infers `MACOS_NOTARY_KEY_ID` from `AuthKey_<KEYID>.p8` when possible
- requires `MACOS_NOTARY_ISSUER_ID` explicitly because Apple does not store it in the `.p8` file

Store the emitted values in GitHub under Settings, Secrets and variables, Actions.

## Example Files

The shipped example configurations live under:

- `src/mcsas3gui/configurations/readdata`
- `src/mcsas3gui/configurations/run`
- `src/mcsas3gui/configurations/histogram`
- `src/mcsas3gui/configurations/prefab`

The shipped example datasets live under:

- `src/mcsas3gui/testdata`

Read configurations declare source data units with `QUnits: "1/nm"` and `IUnits: "1/(m sr)"`.
Run configurations keep `logRandom: true` enabled, which is the recommended standard mode for
log-uniform parameter sampling.

## Structure

The GUI is organized into:

- `gui/main_window.py` for tab assembly
- `gui/*_tab.py` modules for tab-specific UI behavior
- `gui/mcsas3_bridge.py` for canonical McSAS3 integration
- `gui/optimization_worker.py` and `utils/base_worker.py` for background execution
- shared GUI helpers in `gui/*_helpers.py` and `utils/task_runner_mixin.py`

The generated dependency overview is documented in
[the GUI structure page](https://bamresearch.github.io/mcsas3gui/structure.html).

## Documentation

https://BAMresearch.github.io/mcsas3gui

## Development

### Contributing

We welcome contributions! Please ensure your code follows the project's coding style and includes relevant tests and documentation.

### License

This project is licensed under the MIT license

### Testing

See which tests are available (arguments after `--` get passed to *pytest* which runs the tests):

    tox -e py -- --co

Run a specific test only:

    tox -e py -- -k <test_name from listing before>

Run all tests with:

```bash
tox -e py
```

### Package Version

Get the next version number and how the GIT history would be interpreted for that:

    pip install python-semantic-release
    semantic-release -v version --print

This prints its interpretation of the commits in detail. Make sure to supply the `--print`
argument to not raise the version number which is done automatically by the *release* job
of the GitHub Action Workflows.

### Project template

Update the project configuration from the *copier* template and make sure the required packages
are installed:

    pip install copier jinja2-time
    copier update --trust --skip-answered
