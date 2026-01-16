Overview
========

The **colorwheel** project generates a high-quality RGB color wheel image
with customizable markers and a side legend detailing each color.

Installation
------------

Install the package and development dependencies::

  pip install .
  pip install -e .
  pip install -r requirements-dev.txt  # includes Sphinx, pytest, etc.

Usage
-----

Run the CLI to generate an image::

  python apps/main.py --output wheel.png

To use data from an ODS file::

  python apps/main.py --use-data --data-file data/golden.ods

Demo
----

Example of a generated color wheel with legend:

.. image:: ../../data/golden.png
   :alt: Generated color wheel with legend
   :width: 600px

Interactive Converter UI example:

.. image:: ../../data/ui.png
   :alt: Textual-based interactive converter UI
   :width: 600px

Note: after updating `data/golden.ods`, run:

  make regenerate-golden
  make test
  to regenerate golden reference files and ensure tests pass.

Documentation
-------------

To build the docs locally::

  make docs-html
  make docs-man
  make docs-pdf

Released docs are tracked in the ``docs/released/html`` directory.

API Reference
-------------

See the :doc:`modules` section for the full API reference.
