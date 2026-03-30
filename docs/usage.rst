=====
Usage
=====

Launching
=========

Start the GUI with:

.. code-block:: bash

   mcsas3gui

Tab Workflow
============

The maintained GUI workflow is:

1. **Data Loading**:
   choose a read-configuration YAML and a test dataset, then inspect the raw, clipped, and binned
   data stages in the preview plot.
2. **Run Settings**:
   choose a run configuration YAML and preview a single repetition on the currently loaded data.
3. **McSAS3 Optimization**:
   select one or more input files plus the read/run configuration files and launch the full
   optimization worker.
4. **Histogram Settings** and **Run Histogramming**:
   configure histogram generation and run it on McSAS3 result files.

Canonical Core Integration
==========================

McSAS3GUI now talks to McSAS3 through the maintained canonical workflow surface:

- data loading is done through ``prepare_1d_processing_data_from_file()``
- plotting is derived from canonical ``ProcessingData`` stages
- optimization preview and full optimization both use the current McSAS3 workflow/runtime surface
- histogramming is launched through explicit CLI argument lists rather than shell-style command
  strings

Abortable Runs
==============

The optimization preview and the main optimization run can be aborted in place. When active, the
buttons switch to ``Running... Click to abort.`` and forward a stop request to the core McSAS3
runner.
