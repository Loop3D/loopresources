"""
Find Drillhole intersection
=============================

This example demonstrates the basic usage of the DrillholeDatabase class
for a single drillhole and finding the intersection with a LoopStructural function
and visualising the model, drillhole and intersection point using Loop3DView/Pyvista
"""

import pandas as pd
from loopresources import DrillholeDatabase
import pyvista as pv
import numpy as np
from LoopStructural import GeologicalModel
from LoopStructural.utils import strikedip2vector
from LoopStructural.visualisation import Loop3DView

#############################################################################
# Create our LoopStrutural Model
# -----------------------------
model = GeologicalModel([0, 0, 0], [10, 10, 10])
data = pd.DataFrame(
    {
        "X": [1, 2, 3, 4, 5],
        "Y": [5, 5, 5, 5, 5],
        "Z": [10, 10, 10, 10, 10],
        "val": [0] * 5,
        "nx": [4.32978028e-17] * 5,
        "ny": [-7.07106781e-01] * 5,
        "nz": [7.07106781e-01] * 5,
        'feature_name': ['fault'] * 5,
    }
)
model.create_and_add_fault('fault', displacement=1.0, data=data)

#############################################################################
# Create Drillhole Data
# -----------------------------
collar = pd.DataFrame(
    {
        "HOLEID": ["DH1"],
        "EAST": [0],
        "NORTH": [0],
        "RL": [10],
        "DEPTH": [5],
    }
)
survey = pd.DataFrame(
    {
        "HOLEID": ["DH1", "DH1", "DH1"],
        "DEPTH": [0, 2, 5],
        "AZIMUTH": [0, 0, 0],
        "DIP": [-60, -62, -50],
    }
)

dhdb = DrillholeDatabase(survey=survey, collar=collar)

#############################################################################
# Find Intersection
# -----------------------------
# Find intersection of drillhole with geological model fault
# LoopStructural uses a global and local coordinate system, we need to ensure that
# the implicit functions are evaluated using the global coordinates.
# To do this we can use the model.evaluate_feature_value(feature_name, coords) method
# The `find_implicit_function_intersection` method of the DrillHole class can be used to find the intersection.
# It requires a function that takes coords as an input and returns the implicit function value.
# We can use a lambda function to wrap the model's method.
#

pts = dhdb["DH1"].find_implicit_function_intersection(
    lambda xyz: model.evaluate_feature_value('fault', xyz)
)
print(f"\nIntersection points: \n {pts}")

viewer = Loop3DView(model)
viewer.plot_surface(model['fault'], 0.0)
viewer.add_mesh(model.bounding_box.vtk().outline(), color='black')
viewer.add_mesh(dhdb['DH1'].vtk())
viewer.add_points(pts[['x', 'y', 'z']].values, color='blue', point_size=10)
viewer.show()

#############################################################################
# We can also calculate the orientation of the implicit function at the intersection points

normals = model.evaluate_feature_gradient('fault', pts[['x', 'y', 'z']].values)
print(f"\nIntersection normals: \n {normals}")