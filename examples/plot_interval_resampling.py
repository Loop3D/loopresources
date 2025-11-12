"""
=====================================
Interval Resampling and VTK Properties
=====================================

This example demonstrates how to:

1. Resample irregular interval data (like lithology logs) to regular intervals
2. Handle overlapping intervals by selecting the value with biggest occurrence
3. Attach resampled properties to VTK visualizations as cell data

"""

from loopresources.drillhole.drillhole_database import DrillholeDatabase
from loopresources.drillhole.dhconfig import DhConfig
import pandas as pd

###############################################################################
# Setup: Create sample drillhole data
# ------------------------------------

# Create collar data
collar = pd.DataFrame(
    {
        DhConfig.holeid: ["DH001"],
        DhConfig.x: [100.0],
        DhConfig.y: [1000.0],
        DhConfig.z: [50.0],
        DhConfig.total_depth: [100.0],
    }
)

# Create survey data
survey = pd.DataFrame(
    {
        DhConfig.holeid: ["DH001", "DH001"],
        DhConfig.depth: [0.0, 50.0],
        DhConfig.azimuth: [0.0, 0.0],
        DhConfig.dip: [90.0, 90.0],
    }
)

# Create irregular lithology data (realistic sampling)
lithology = pd.DataFrame(
    {
        DhConfig.holeid: ["DH001", "DH001", "DH001", "DH001"],
        DhConfig.sample_from: [0.0, 10.0, 25.0, 50.0],
        DhConfig.sample_to: [10.0, 25.0, 50.0, 100.0],
        "LITHO": ["Granite", "Schist", "Granite", "Sandstone"],
    }
)

# Create database
db = DrillholeDatabase(collar, survey)
db.add_interval_table("lithology", lithology)

###############################################################################
# Example 1: Resample to regular 1m intervals
# --------------------------------------------

hole = db["DH001"]
resampled_1m = hole.resample("lithology", ["LITHO"], new_interval=1.0)

print("Original irregular intervals:")
print(lithology[["SAMPFROM", "SAMPTO", "LITHO"]])
print()

print(f"Resampled to regular 1m intervals ({len(resampled_1m)} total):")
print(resampled_1m.head(15))
print()

###############################################################################
# Example 2: Resample to 5m intervals
# ------------------------------------

resampled_5m = hole.resample("lithology", ["LITHO"], new_interval=5.0)

print(f"Resampled to regular 5m intervals ({len(resampled_5m)} total):")
print(resampled_5m)
print()

###############################################################################
# Example 3: Mode selection with overlapping intervals
# -----------------------------------------------------

# The 25-30m interval demonstrates mode selection
# It overlaps with:
#   - Schist (10-25m): 0m overlap at boundary
#   - Granite (25-50m): 5m overlap (full interval)
# Result: Granite is selected (bigger occurrence)

interval_25_30 = resampled_5m[resampled_5m[DhConfig.sample_from] == 25.0]
print("Mode selection example (25-30m interval):")
print("  Original intervals: Schist (10-25m) and Granite (25-50m)")
print(f"  Selected value: {interval_25_30['LITHO'].values[0]} (5m vs 0m)")
print()

###############################################################################
# Example 4: VTK visualization with properties
# ---------------------------------------------

try:
    import pyvista as pv  # noqa: F401

    # Create VTK tube with lithology as cell property
    tube = hole.vtk(newinterval=5.0, properties=["lithology"])

    print("VTK tube created with lithology property:")
    print(f"  Points: {tube.n_points}")
    print(f"  Cells: {tube.n_cells}")
    print(f"  Cell data arrays: {list(tube.cell_data.keys())}")
    print(f"  Lithology values: {tube.cell_data['lithology_LITHO']}")
    print()

    # For visualization (requires display):
    # plotter = pv.Plotter()
    # plotter.add_mesh(tube, scalars='lithology_LITHO', cmap='viridis')
    # plotter.show()

except ImportError:
    print("PyVista not installed - VTK creation skipped")
    print("Install with: pip install pyvista")
    print()
    print("Example usage:")
    print("  tube = hole.vtk(newinterval=1.0, properties=['lithology'])")
    print("  # Properties attached as cell data: lithology_LITHO")

###############################################################################
# Example 5: Multiple properties
# -------------------------------

# You can attach multiple properties at once
print("Multiple properties example:")
print("  tube = hole.vtk(newinterval=1.0, properties=['lithology', 'assays'])")
print("  # Creates cell data: lithology_LITHO, assays_AU_ppm, assays_CU_pct")
print()

# For entire database:
print("Database-level VTK:")
print("  multiblock = db.vtk(newinterval=1.0, properties=['lithology'])")
print("  # Creates multiblock with all drillholes")
