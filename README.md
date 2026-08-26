# McSAS3GUI (v0.2.1)

[![PyPI Package latest release](https://img.shields.io/pypi/v/mcsas3gui.svg)](https://pypi.org/project/mcsas3gui)
[![Commits since latest release](https://img.shields.io/github/commits-since/BAMresearch/mcsas3gui/v0.2.1.svg)](https://github.com/BAMresearch/mcsas3gui/compare/v0.2.1...main)
[![License](https://img.shields.io/pypi/l/mcsas3gui.svg)](https://en.wikipedia.org/wiki/MIT_license)
[![Supported versions](https://img.shields.io/pypi/pyversions/mcsas3gui.svg)](https://pypi.org/project/mcsas3gui)
[![PyPI Wheel](https://img.shields.io/pypi/wheel/mcsas3gui.svg)](https://pypi.org/project/mcsas3gui#files)
[![Weekly PyPI downloads](https://img.shields.io/pypi/dw/mcsas3gui.svg)](https://pypi.org/project/mcsas3gui/)
[![Continuous Integration and Deployment Status](https://github.com/BAMresearch/mcsas3gui/actions/workflows/ci-cd.yml/badge.svg)](https://github.com/BAMresearch/mcsas3gui/actions/workflows/ci-cd.yml)
[![Coverage report](https://img.shields.io/endpoint?url=https://BAMresearch.github.io/mcsas3gui/coverage-report/cov.json)](https://BAMresearch.github.io/mcsas3gui/coverage-report/)

A graphical user interface for the canonical McSAS3 workflow.

McSAS3GUI is a thin desktop client over the maintained McSAS3 public API. It loads data through
the canonical `ProcessingData` workflow, previews fits, runs optimizations, and launches
histogramming without depending on removed legacy McSAS3 internals.

## Installation

McSAS3GUI requires Python 3.12 or newer.

Install the released GUI package with `pip`:

```bash
pip install mcsas3gui
```

If you use `uv`, create and activate a Python 3.12+ environment, then install the same package with:

```bash
uv venv --python 3.12
source .venv/bin/activate
uv pip install mcsas3gui
```

On Windows, activate the environment with `.venv\Scripts\activate` instead of `source`.

You can also install the in-development version with `pip`:

```bash
pip install git+https://github.com/BAMresearch/mcsas3gui.git@main
```

or, from a local source checkout with `uv`:

```bash
uv venv --python 3.12
source .venv/bin/activate
uv pip install ../McSAS3 .
mcsas3gui --version
```

Run the local source command from the `McSAS3GUI` repository with the `McSAS3` repository checked
out next to it.

For prebuilt standalone binaries (Linux, macOS, Windows), see the latest GitHub release:

- https://github.com/BAMresearch/mcsas3gui/releases/latest

Release assets are built for tagged releases. The macOS release asset is code-signed.

## Running the Application

After activating the environment, the preferred launch commands are:

```bash
mcsas3gui
```

or the short alias:

```bash
m3gui
```

The module form also works:

```bash
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

## Quick Start

1. Open the **Getting Started** tab and choose one of the shipped prefab workflows, or configure
   the tabs manually.
2. In **Data Loading**, choose a read-configuration YAML and a test dataset.
3. In **Run Settings**, choose a run configuration and preview a single repetition.
4. In **McSAS3 Optimization**, launch the full optimization for one or more files.
5. In **Histogram Settings** and **Run Histogramming**, configure and run histogram generation on
   the result files.

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

Both optimization buttons are abortable. While running, they change to
`Running... Click to abort.` and forward a stop request to the core McSAS3 runner.

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
