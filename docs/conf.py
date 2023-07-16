#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# minimalmodbus documentation build configuration file, created by
# sphinx-quickstart on Tue Jul  9 22:26:36 2013.

import os
import sys
import time

# If extensions (or modules to document with autodoc) are in another
# directory, add these directories to sys.path here. If the directory is
# relative to the documentation root, use os.path.abspath to make it
# absolute, like shown here.
# sys.path.insert(0, os.path.abspath('.'))

# Get the project root dir, which is the parent dir of this
cwd = os.getcwd()
project_root = os.path.dirname(cwd)

# Insert the project root dir as the first element in the PYTHONPATH.
# This lets us ensure that the source package is imported, and that its
# version is used.
sys.path.insert(0, project_root)

tests_directory = os.path.join(project_root, "tests")
sys.path.insert(0, tests_directory)

import minimalmodbus  # noqa

# -- General configuration ---------------------------------------------

# Add any Sphinx extension module names here, as strings. They can be
# extensions coming with Sphinx (named 'sphinx.ext.*') or your custom ones.
extensions = [
    "sphinx.ext.autodoc",
    "sphinx.ext.viewcode",
    "sphinxcontrib.programoutput",
]

# Add any paths that contain templates here, relative to this directory.
templates_path = ["_templates"]

# The suffix of source filenames.
source_suffix = ".rst"

# The master toctree document.
master_doc = "index"

# General information about the project.
project = "MinimalModbus"
copyright = time.strftime("%Y") + ", Jonas Berg"

# The version info for the project you're documenting, acts as replacement
# for |version| and |release|, also used in various other places throughout
# the built documents.
#
# The short X.Y version.
version = minimalmodbus.__version__
# The full version, including alpha/beta/rc tags.
release = minimalmodbus.__version__

# List of patterns, relative to source directory, that match files and
# directories to ignore when looking for source files.
exclude_patterns = ["_build", "setup.py", "tests"]

pygments_style = "sphinx"

autodoc_member_order = "bysource"

# -- Options for HTML output -------------------------------------------

html_theme = "sphinx_rtd_theme"
html_last_updated_fmt = "%Y-%m-%d %H:%M"

# Output file base name for HTML help builder.
htmlhelp_basename = "minimalmodbusdoc"


# -- Options for LaTeX output ------------------------------------------

latex_elements = {
    # The paper size ('letterpaper' or 'a4paper').
    #'papersize': 'letterpaper',
    # The font size ('10pt', '11pt' or '12pt').
    #'pointsize': '10pt',
    # Additional stuff for the LaTeX preamble.
    #'preamble': '',
}

# Grouping the document tree into LaTeX files. List of tuples
# (source start file, target name, title, author, documentclass
# [howto/manual]).
latex_documents = [
    (
        "index",
        "minimalmodbus.tex",
        "MinimalModbus Documentation",
        "Jonas Berg",
        "manual",
    ),
]
