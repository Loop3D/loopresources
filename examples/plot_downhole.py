"""
Downhole plotting
================

Example showing downhole line, categorical, and image plots.
"""

import matplotlib.pyplot as plt
import pandas as pd

from loopresources.drillhole.dhconfig import DhConfig
from loopresources.drillhole.drillhole_database import DrillholeDatabase

collar = pd.DataFrame(
    {
        DhConfig.holeid: ["DH001", "DH002", "DH003"],
        DhConfig.x: [100.0, 200.0, 300.0],
        DhConfig.y: [1000.0, 2000.0, 3000.0],
        DhConfig.z: [50.0, 60.0, 70.0],
        DhConfig.total_depth: [150.0, 200.0, 180.0],
    }
)

survey = pd.DataFrame(
    {
        DhConfig.holeid: ["DH001", "DH001", "DH002", "DH002", "DH003"],
        DhConfig.depth: [0.0, 100.0, 0.0, 120.0, 0.0],
        DhConfig.azimuth: [0.0, 0.0, 45.0, 45.0, 90.0],
        DhConfig.dip: [-90.0, -90.0, -85.0, -80.0, -90.0],
    }
)

db = DrillholeDatabase(collar, survey)

lithology = pd.DataFrame(
    {
        DhConfig.holeid: ["DH001", "DH001", "DH002", "DH002", "DH003"],
        DhConfig.sample_from: [0.0, 50.0, 0.0, 80.0, 0.0],
        DhConfig.sample_to: [50.0, 150.0, 80.0, 200.0, 180.0],
        "LITHO": ["Granite", "Schist", "Sandstone", "Shale", "Limestone"],
    }
)

assays = pd.DataFrame(
    {
        DhConfig.holeid: ["DH001", "DH001", "DH002", "DH002", "DH003"],
        DhConfig.sample_from: [0.0, 75.0, 0.0, 100.0, 0.0],
        DhConfig.sample_to: [75.0, 150.0, 100.0, 200.0, 180.0],
        "AU_ppm": [0.1, 2.5, 0.05, 1.2, 0.4],
    }
)

db.add_interval_table("lithology", lithology)
db.add_interval_table("assays", assays)

# Line plot (numeric values)
db.plot_downhole("assays", "AU_ppm", kind="line", layout="grid", ncols=2)
plt.tight_layout()
plt.show()

# Categorical plot
db.plot_downhole("lithology", "LITHO", kind="categorical", step=2.0, layout="grid", ncols=2)
plt.tight_layout()
plt.show()

# Image plot (numeric heatmap)
db.plot_downhole("assays", "AU_ppm", kind="image", step=2.0, layout="grid", ncols=2)
plt.tight_layout()
plt.show()
