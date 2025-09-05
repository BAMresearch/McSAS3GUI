# McSAS3GUI (v0.1.5)

[![PyPI Package latest release](https://img.shields.io/pypi/v/mcsas3gui.svg)](https://test.pypi.org/project/mcsas3gui)
[![Commits since latest release](https://img.shields.io/github/commits-since/BAMresearch/mcsas3gui/v0.1.5.svg)](https://github.com/BAMresearch/mcsas3gui/compare/v0.1.5...main)
[![License](https://img.shields.io/pypi/l/mcsas3gui.svg)](https://en.wikipedia.org/wiki/MIT_license)
[![Supported versions](https://img.shields.io/pypi/pyversions/mcsas3gui.svg)](https://test.pypi.org/project/mcsas3gui)
[![PyPI Wheel](https://img.shields.io/pypi/wheel/mcsas3gui.svg)](https://test.pypi.org/project/mcsas3gui#files)
[![Weekly PyPI downloads](https://img.shields.io/pypi/dw/mcsas3gui.svg)](https://test.pypi.org/project/mcsas3gui/)
[![Continuous Integration and Deployment Status](https://github.com/BAMresearch/mcsas3gui/actions/workflows/ci-cd.yml/badge.svg)](https://github.com/BAMresearch/mcsas3gui/actions/workflows/ci-cd.yml)
[![Coverage report](https://img.shields.io/endpoint?url=https://BAMresearch.github.io/mcsas3gui/coverage-report/cov.json)](https://BAMresearch.github.io/mcsas3gui/coverage-report/)

A graphical user interface for the McSAS3 software.

## Installation

    pip install mcsas3gui

You can also install the in-development version with:

    pip install git+https://github.com/BAMresearch/mcsas3gui.git@main

## Running the Application

    python3 -m mcsas3gui

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

    tox -e py

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

