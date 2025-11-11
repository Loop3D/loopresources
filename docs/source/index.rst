.. Resources documentation master file, created by
   sphinx-quickstart on Thu Oct 26 10:15:20 2023.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

LoopResources
=====================================
.. image:: static/loopresources_logo.png
   :alt: LoopResources logo
   :align: center
   :width: 100%

.. important::
   LoopResources is currently in active development. While the core functionality is stable, some APIs may change in future releases.
   Currently only the drillhole database functionality is implemented, with a link to LoopStructural and resource modelling tools to follow.

Overview
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

**LoopResources** is a Python library designed for subsurface resource modelling workflows.
It provides a database interface for managing drillhole data with a vision for easy integration into LoopStructural
and subsequent resource modelling.

To install LoopResources, use pip:
.. code-block:: bash

   pip install loopresources

optional dependencies for VTK support can be installed via:
.. code-block:: bash

   pip install loopresources[vtk]


The library has three main goals:



1. **Provide a Pythonic interface for drillhole databases**

   .. code-block:: python

      from loopresources import DrillholeDatabase
      import pandas as pd

      db = DrillholeDatabase.from_csv(
          survey_csv="survey.csv",
          collar_csv="collar.csv",
          assay_csv="assay.csv",
      )
      db.add_table("lithology", pd.read_csv(lithology_df))
      desurveyed_lithology = db.desurvey_intervals("lithology")
      vtk_objects = []
      for h in db:
          vtk_objects.append(h.to_vtk())


2. **Integrate with implicit geological modelling via LoopStructural**

   A direct link between LoopStructural and LoopResources for easy building and update of geological models from drillhole data.

3. **Enable resource modelling and domaining workflows**

   The library provides tools for using LoopStructural surfaces for geological domaining and supports interoperability with third-party geostatistical packages for grade estimation, simulation, and uncertainty analysis.
   
   .. toctree::
      :hidden:

      auto_examples/index
      tutorials/index

   .. toctree::
      :hidden:

      _autosummary/loopresources

   