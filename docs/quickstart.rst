==========
Quickstart
==========

Launch McSAS3GUI
================

After installation, start the application with one of:

.. code-block:: bash

   mcsas3gui
   m3gui
   python -m mcsas3gui

If you are developing `McSAS3GUI` alongside a sibling `McSAS3` checkout, the GUI bootstrap layer
will prefer `../McSAS3/src` automatically when the installed `mcsas3` package is too old for the
maintained canonical GUI workflow.

Run A First Analysis
====================

The shortest path through the GUI is:

1. Open the **Getting Started** tab and choose one of the shipped prefab workflows.
2. In **Data Loading**, load a test dataset and a read-configuration YAML.
3. In **Run Settings**, select a run configuration and use
   **Test single repetition on loaded Test Data** to preview the fit.
4. In **McSAS3 Optimization**, select one or more input files and run the full optimization.
5. In **Histogram Settings** and **Run Histogramming**, configure histogram generation and run it
   on the optimization result files.

Built-in example configurations live under:

- ``src/mcsas3gui/configurations/readdata``
- ``src/mcsas3gui/configurations/run``
- ``src/mcsas3gui/configurations/histogram``
- ``src/mcsas3gui/configurations/prefab``

Built-in example datasets live under:

- ``src/mcsas3gui/testdata``

The shipped read configurations declare source units with ``QUnits: "1/nm"`` and
``IUnits: "1/(m sr)"``. The run configurations keep ``logRandom: true`` enabled, which is the
recommended standard mode for log-uniform parameter sampling.

The shipped run configurations also show ``fitPorodBackground: false``. Change it to ``true`` to
fit an optional non-negative additive ``q^-4`` background. This requires strictly positive fitted
Q magnitudes and can affect the recovered low-Q particle distribution.

Abort Running Tasks
===================

The long-running optimization buttons are abortable:

- **Run McSAS3 Optimization ...**
- **Test single repetition on loaded Test Data**

While active, each button switches to ``Running... Click to abort.``. Clicking it again requests a
clean stop through the core McSAS3 cancellation hook.
