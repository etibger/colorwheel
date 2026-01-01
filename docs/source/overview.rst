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

  python main.py --output wheel.png

To use data from an ODS file::

  python main.py --use-data --data-file data/golden.ods

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
