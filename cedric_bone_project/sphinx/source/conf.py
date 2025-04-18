# Configuration file for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

# -- Project information -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information

import os
import sys
sys.path.insert(0, os.path.abspath('../../')) # Point to project root directory

project = 'P2P File Sharing Software'
copyright = '2025, Cedric Bone'
author = 'Cedric Bone'

# -- General configuration ---------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#general-configuration

extensions = [
    'sphinx.ext.autodoc',    # Include documentation from docstrings
    'sphinx.ext.napoleon',   # Support for Google and NumPy style docstrings
    'sphinx.ext.viewcode',   # Add links to source code
]

templates_path = ['_templates']
exclude_patterns = []


today = 'April 18, 2025'

# -- Options for HTML output -------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#options-for-html-output

html_theme = 'alabaster'
html_static_path = ['_static']
