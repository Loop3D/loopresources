import pandas as pd
from loopresources import DrillholeDatabase
import pyvista as pv
import numpy as np

collar = pd.DataFrame({
   "HOLEID": ["DH1"],
   "EAST": [0],
   "NORTH": [0],
   "RL": [0],
   "DEPTH": [100],
})
survey = pd.DataFrame({
   "HOLEID": ["DH1", "DH1", "DH1"],
   "DEPTH": [0, 50, 100],
   "AZIMUTH": [0, 0, 0],
   "DIP": [-10, -12, -50],
})

dhdb = DrillholeDatabase(survey=survey, collar=collar)
p = pv.Plotter()
p.add_points(np.array([[0,0,0]]), color="red", point_size=10)
p.add_mesh(dhdb["DH1"].vtk())
p.add_axes()
p.show()