# Configuration file for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

# -- Project information -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information
import os
import sys

sys.path.insert(0, os.path.abspath("../.."))
import loopresources as lr

project = "LoopResources"
copyright = "2023, Lachlan Grose"
author = "Lachlan Grose"
release = lr.__version__

# -- General configuration ---------------------------------------------------
autoclass_content = "both"  # include both class docstring and __init__
autodoc_default_flags = [
    # Make sure that any autodoc declarations show the right members
    "members",
    "inherited-members",
    "private-members",
    "show-inheritance",
]
autosummary_generate = True  # Make _autosummary files and include them
napoleon_numpy_docstring = True  # False  # Force consistency, leave only Google
napoleon_use_rtype = False  # More legible
autosummary_imported_members = True
autosummary_ignore_module_all = False
# Add any Sphinx extension module names here, as strings. They can be
# extensions coming with Sphinx (named 'sphinx.ext.*') or your custom
# ones.
extensions = [
    # Need the autodoc and autosummary packages to generate our docs.
    "sphinx.ext.autodoc",
    "sphinx.ext.autosummary",
    # The Napoleon extension allows for nicer argument formatting.
    "sphinx.ext.napoleon",
    # add sphinx gallery
    "sphinx_gallery.gen_gallery",
    # citations
    "myst_parser",
]

# Add any paths that contain templates here, relative to this directory.
templates_path = ["_templates"]

# Sphinx Gallery configuration
sphinx_gallery_conf = {
    "examples_dirs": "../../examples",  # path to your example scripts
    "gallery_dirs": "auto_examples",  # path to where to save gallery generated output
    "filename_pattern": "/plot_",  # pattern to match example files
    "ignore_pattern": "__init__\.py",  # ignore __init__.py files
    "download_all_examples": False,
    "min_reported_time": 0,
    "thumbnail_size": (200, 200),
    "abort_on_example_error": False,
}

# List of patterns, relative to source directory, that match files and
# directories to ignore when looking for source files.
# This pattern also affects html_static_path and html_extra_path.
exclude_patterns = []

html_theme_options = {
    "icon_links": [
        {
            "name": "GitHub",
            "url": "https://github.com/loop3d/LoopStructural",
            "icon": "fab fa-github-square",
        },
        {
            "name": "Twitter",
            "url": "https://twitter.com/loop3d",
            "icon": "fab fa-twitter-square",
        },
    ],
    #     "navbar_start": ["navbar-logo", "navbar-version"],
    #     "use_edit_page_button": True,
    "external_links": [
        {"name": "Loop3d", "url": "https://www.loop3d.org"},
    ],
}
# -- Options for HTML output -------------------------------------------------

# The theme to use for HTML and HTML Help pages.  See the documentation for
# a list of builtin themes.
#
html_theme = "pydata_sphinx_theme"

# Add any paths that contain custom static files (such as style sheets) here,
# relative to this directory. They are copied after the builtin static files,
# so a file named "default.css" will overwrite the builtin "default.css".
html_static_path = ["_static"]
