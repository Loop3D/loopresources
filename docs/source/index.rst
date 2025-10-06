.. Resources documentation master file, created by
   sphinx-quickstart on Thu Oct 26 10:15:20 2023.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

LoopResources
=====================================

Overview
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

LoopResources
=============

**LoopResources** is a Python library designed to streamline subsurface resource modelling workflows by integrating geological data management, implicit modelling, and geostatistical analysis in a unified framework.

The library has three main goals:

1. **Provide a Pythonic interface for drillhole databases**

   LoopResources offers a consistent, object-oriented API for working with drillhole data from diverse sources. It enables efficient querying, manipulation, and visualization of drillhole and assay data, with built-in support for validation and metadata tracking.

2. **Integrate with implicit geological modelling via `LoopStructural <https://loop3d.github.io/LoopStructural/>`_**

   Seamless integration with LoopStructural allows users to build and update 3D geological models directly from drillhole data and geological interpretations. LoopResources bridges data and model domains, simplifying workflows that move from raw data to structural models.

3. **Enable resource modelling and domaining workflows**

   The library provides tools for using LoopStructural surfaces for geological domaining and supports interoperability with third-party geostatistical packages for grade estimation, simulation, and uncertainty analysis.

.. toctree::
   :maxdepth: 2
   :caption: Contents:

   auto_examples/index
   tutorials/index

Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`

  .. toctree::
   :caption: LoopResources API
   :hidden:

.. autosummary::
   :caption: API
   :toctree: _autosummary
   :template: custom-module-template.rst
   :recursive:

   loopresources
