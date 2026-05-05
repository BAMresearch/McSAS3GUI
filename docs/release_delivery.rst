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

Release assets workflow
=======================

The repo includes ``.github/workflows/standalone-release.yml`` for tagged releases.

This workflow:

- triggers on GitHub release publication (tags)
- builds standalone archives for Linux, macOS, and Windows
- code-signs the macOS app bundle
- notarizes and staples the macOS app bundle
- uploads the produced archives to the corresponding GitHub release

Required GitHub secrets for macOS signing and notarization:

- ``MACOS_CERT_P12_BASE64``: base64-encoded ``.p12`` certificate export
- ``MACOS_CERT_P12_PASSWORD``: password used when exporting the ``.p12``
- ``MACOS_CODESIGN_IDENTITY``: certificate identity string selected from the ``.p12``
- ``MACOS_KEYCHAIN_PASSWORD``: temporary runner keychain password
- ``MACOS_NOTARY_KEY_ID``: App Store Connect API key id
- ``MACOS_NOTARY_ISSUER_ID``: App Store Connect issuer UUID
- ``MACOS_NOTARY_API_KEY``: raw contents of the App Store Connect ``.p8`` key file

One-time local preparation of the GitHub secrets
================================================

The repository includes ``tools/prepare_github_secrets.sh`` to prepare every macOS standalone
release secret in one pass.

Example usage:

.. code-block:: bash

   tools/prepare_github_secrets.sh \
     --p12-path ~/Downloads/mcsas3gui-signing-cert.p12 \
     --p12-password '<p12-password>' \
     --p8-path ~/Downloads/AuthKey_ABC123XYZ.p8 \
     --issuer-id 12345678-1234-1234-1234-123456789abc

The helper script:

- base64-encodes the signing certificate as ``MACOS_CERT_P12_BASE64``
- emits the provided ``.p12`` password as ``MACOS_CERT_P12_PASSWORD``
- imports the ``.p12`` into a temporary macOS keychain to discover
  ``MACOS_CODESIGN_IDENTITY``
- emits the selected temporary keychain password as ``MACOS_KEYCHAIN_PASSWORD``
- reads the raw ``.p8`` contents into ``MACOS_NOTARY_API_KEY``
- infers ``MACOS_NOTARY_KEY_ID`` from ``AuthKey_<KEYID>.p8`` when possible
- requires ``MACOS_NOTARY_ISSUER_ID`` explicitly because Apple does not include it in the
  private key file

After running the helper, store the printed values in GitHub under Settings, Secrets and
variables, Actions.

Release build and verification flow
===================================

For each macOS release build, the workflow performs these steps:

- imports the signing certificate into a temporary runner keychain
- signs the PyInstaller macOS bundle with the selected Developer ID identity
- archives the bundle and submits it to Apple notarization with ``xcrun notarytool submit --wait``
- staples the notarization ticket with ``xcrun stapler staple``
- validates the stapled bundle with ``xcrun stapler validate``
- runs a final policy check with ``spctl -a -vvv --type exec``
- rebuilds the distributable zip archive after signing and stapling

Verification done in CI:

- ``codesign --verify --deep --strict`` on the app bundle
- ``xcrun stapler validate`` on the stapled app bundle
- ``spctl -a -vvv --type exec`` to confirm the notarized app satisfies macOS policy
- archive rebuilt after signing and stapling so the uploaded macOS zip contains notarized binaries
