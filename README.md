# McSAS3GUI (v0.1.6)

[![PyPI Package latest release](https://img.shields.io/pypi/v/mcsas3gui.svg)](https://pypi.org/project/mcsas3gui)
[![Commits since latest release](https://img.shields.io/github/commits-since/BAMresearch/mcsas3gui/v0.1.6.svg)](https://github.com/BAMresearch/mcsas3gui/compare/v0.1.6...main)
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

```bash
pip install mcsas3gui
```

You can also install the in-development version with:

```bash
pip install git+https://github.com/BAMresearch/mcsas3gui.git@main
```

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
[the tracked GUI dependency diagram](https://bamresearch.github.io/mcsas3gui/generated_module_dependencies.html).

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
