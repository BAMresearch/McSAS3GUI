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
- the build currently expects sibling ``McSAS3`` and ``MoDaCor`` source checkouts so the bundled
  GUI and histogram helper use the same canonical core stack
- by default the builder looks for:

  - ``../McSAS3/src``
  - ``../MoDaCor/src``

- you can override those locations with:

  - ``MCSAS3GUI_MCSAS3_SRC=/path/to/McSAS3/src``
  - ``MCSAS3GUI_MODACOR_SRC=/path/to/MoDaCor/src``

- the local builder smoke-tests the frozen GUI with ``--smoke-test`` in headless mode
- the bundled histogram helper is validated with ``--help``

CI workflow
===========

The repo includes ``.github/workflows/standalone.yml`` which builds standalone archives on:

- Linux
- macOS
- Windows

The workflow checks out the sibling ``McSAS3`` and ``MoDaCor`` repositories explicitly and passes
their source roots into the standalone build step.
