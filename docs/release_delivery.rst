================
Release delivery
================

McSAS3GUI now has two delivery tracks:

- standard Python package delivery via wheel and sdist
- standalone GUI bundles for macOS, Windows, and Linux

Python packages
===============

The existing package build remains:

- ``python -m build``
- ``tox -e build``

This produces:

- a source distribution
- a wheel for normal Python installation

Standalone GUI bundles
======================

The standalone build path packages:

- the windowed ``McSAS3GUI`` application
- a bundled ``mcsas3-histogrammer`` helper executable for the histogramming tabs

Local build command:

.. code-block:: bash

   tox -e standalone

This runs ``tools/build_standalone.py`` and produces:

- ``dist/standalone/<platform-tag>/``: the unpacked standalone bundle
- ``dist/standalone/mcsas3gui-standalone-<platform-tag>.zip``: the distributable archive

Current implementation notes
============================

- the standalone path uses PyInstaller in ``onedir`` mode
- the GUI bundle includes the shipped GUI configurations, resources, and test data
- the build expects a sibling ``McSAS3`` source checkout so the bundled GUI and histogram helper
  use the same canonical core stack
- by default the builder looks for:

  - ``../McSAS3/src``

- you can override that location with:

  - ``MCSAS3GUI_MCSAS3_SRC=/path/to/McSAS3/src``

- the local builder smoke-tests the frozen GUI with ``--smoke-test`` in headless mode
- the bundled histogram helper is validated with ``--help``

CI workflow
===========

The repo includes ``.github/workflows/standalone.yml`` which builds standalone archives on:

- Linux
- macOS
- Windows

The workflow checks out the sibling ``McSAS3`` repository and passes its source root into the
standalone build step.

After the build succeeds, the workflow also verifies the generated standalone manifest and artifact
layout by checking:

- ``dist/standalone/<platform-tag>/build_info.json``
- ``dist/standalone/<platform-tag>/README_STANDALONE.txt``
- ``dist/standalone/mcsas3gui-standalone-<platform-tag>.zip``
- the GUI executable and bundled ``mcsas3-histogrammer`` path recorded in ``build_info.json``
