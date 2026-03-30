============
Installation
============

Install the released GUI package with:

.. code-block:: bash

   pip install mcsas3gui

This installs the GUI together with its McSAS3 core dependency.

Install The Development Version
===============================

To work from source:

.. code-block:: bash

   git clone https://github.com/BAMresearch/McSAS3.git
   git clone https://github.com/BAMresearch/McSAS3GUI.git
   cd McSAS3GUI
   python -m venv .venv
   . .venv/bin/activate
   pip install -e ../McSAS3
   pip install -e .

Launch Commands
===============

After installation, launch the GUI with:

.. code-block:: bash

   mcsas3gui
   m3gui
   python -m mcsas3gui

Development Bootstrap Note
==========================

When running the GUI from source in a workspace that also contains a sibling ``../McSAS3``
checkout, the bootstrap layer will prefer the sibling ``McSAS3/src`` tree automatically if the
installed ``mcsas3`` package does not expose the maintained canonical workflow API yet.
