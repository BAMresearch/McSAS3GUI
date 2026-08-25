=========
Structure
=========

McSAS3GUI is now a thin client over the maintained McSAS3 public API. The GUI no longer depends on
removed McSAS3 internal carriers such as ``McData``; it works with canonical ``ProcessingData`` and
the current McSAS3 workflow entry points through a small bridge layer.

Runtime Overview
================

Runtime flow, at a high level:

1. The main window assembles the tabs.
2. The tabs either call the canonical McSAS3 bridge directly or launch a background worker.
3. The bridge and workers talk to the maintained McSAS3 workflow API or CLI entry points.
4. Shared GUI helpers keep file selection, worker state, and abortable run controls consistent.

Module Responsibilities
=======================

- ``gui/main_window.py`` assembles the application tabs.
- ``gui/data_loading_tab.py`` loads data through the canonical McSAS3 workflow bridge and plots the
  raw, clipped, and binned stages.
- ``gui/run_settings_tab.py`` edits run YAML, previews a single repetition, and visualizes the fit.
- ``gui/optimization_tab.py`` launches full McSAS3 optimizations in a background worker.
- ``gui/hist_settings_tab.py`` and ``gui/hist_run_tab.py`` configure and run histogramming on
  optimized result files.
- ``gui/mcsas3_bridge.py`` is the maintained adapter between GUI plotting/preview code and McSAS3's
  canonical ``ProcessingData`` API.
- ``gui/optimization_worker.py`` and ``utils/base_worker.py`` run long operations off the UI thread.
- ``utils/mcsas3_cli.py`` builds explicit subprocess argument lists for CLI-backed histogram runs.
- ``gui/file_selection_helpers.py``, ``gui/run_control_helpers.py``,
  ``gui/run_settings_helpers.py``, and ``utils/task_runner_mixin.py`` hold the shared GUI glue that
  keeps the tabs small.

Generated Dependency Diagram
============================

The generated module dependency overview is tracked at
:doc:`generated_module_dependencies`. It captures import-level coupling between the maintained
modules in ``src/mcsas3gui``.
