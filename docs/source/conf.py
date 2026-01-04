# Configuration file for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

# -- Path setup --------------------------------------------------------------
# If extensions (or modules to document with autodoc) are in another directory,
# add these directories to sys.path here. If the directory is relative to the
# documentation root, use os.path.abspath to make it absolute.
import os
import sys

# Add project root to sys.path, relative to this conf.py file
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

# -- Project information -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information

project = "colorwheel"
copyright = "2025, Tibor Gerlai"
author = "Tibor Gerlai"

# -- General configuration ---------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#general-configuration

# conf.py

extensions = [
    "sphinx.ext.autodoc",
    "sphinx.ext.autosummary",
    "sphinx.ext.githubpages",
]
autosummary_generate = True  # auto-generate summary tables for modules

templates_path = ["_templates"]
exclude_patterns = []


# -- Options for HTML output -------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#options-for-html-output

html_theme = "alabaster"
html_static_path = ["_static"]


# -- Options for LaTeX output ------------------------------------------------
latex_engine = "pdflatex"
latex_documents = [
    ("index", "colorwheel.tex", "colorwheel Documentation", author, "manual"),
]

# -- Options for manual page output -----------------------------------------
man_pages = [
    ("index", "colorwheel", "colorwheel Documentation", [author], 1),
]
