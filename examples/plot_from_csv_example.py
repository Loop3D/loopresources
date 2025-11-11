"""
DrillholeDatabase.from_csv() Example
=====================================

This example demonstrates how to use the DrillholeDatabase.from_csv() method
to load drilling data directly from CSV files with column mapping.

This is much simpler than manually loading CSVs, creating DataFrames, and
mapping columns yourself.
"""

import os
from loopresources.drillhole import DrillholeDatabase, DhConfig

###############################################################################
# Load Thalanga Data Using from_csv()
# ------------------------------------
# The from_csv() method allows you to load collar and survey data directly
# from CSV files while specifying how the CSV columns map to the required
# DrillholeDatabase columns.

# Get the path to the thalanga data folder
data_folder = os.path.join(".", "thalanga")
collar_file = os.path.join(data_folder, "ThalangaML_collar.csv")
survey_file = os.path.join(data_folder, "ThalangaML_survey.csv")

# Load the data using from_csv with column mapping
db = DrillholeDatabase.from_csv(
    collar_file=collar_file,
    survey_file=survey_file,
    collar_columns={
        "holeid": "HOLE_ID",  # Map 'HOLE_ID' column to holeid
        "x": "X_MGA",  # Map 'X_MGA' column to x
        "y": "Y_MGA",  # Map 'Y_MGA' column to y
        "z": "Z_MGA",  # Map 'Z_MGA' column to z
        "total_depth": "DEPTH",  # Map 'DEPTH' column to total_depth
    },
    survey_columns={
        "holeid": "Drillhole ID",  # Map 'Drillhole ID' column to holeid
        "depth": "Depth",  # Map 'Depth' column to depth
        "azimuth": "Azimuth",  # Map 'Azimuth' column to azimuth
        "dip": "Dip",  # Map 'Dip' column to dip
    },
)

print("✓ Successfully loaded drillhole database using from_csv()")
print(f"  Number of holes: {len(db.list_holes())}")
print(f"  First few holes: {db.list_holes()[:10]}")

###############################################################################
# Compare with Manual Loading
# ----------------------------
# The from_csv() method simplifies what would otherwise require multiple steps:

import pandas as pd

#
# # Load CSV files
collar_raw = pd.read_csv(collar_file)
survey_raw = pd.read_csv(survey_file)
#
# # Manually map columns
collar = pd.DataFrame(
    {
        DhConfig.holeid: collar_raw["HOLE_ID"],
        DhConfig.x: collar_raw["X_MGA"],
        DhConfig.y: collar_raw["Y_MGA"],
        DhConfig.z: collar_raw["Z_MGA"],
        DhConfig.total_depth: collar_raw["DEPTH"],
    }
)
#
survey = pd.DataFrame(
    {
        DhConfig.holeid: survey_raw["Drillhole ID"],
        DhConfig.depth: survey_raw["Depth"],
        DhConfig.dip: survey_raw["Dip"],
        DhConfig.azimuth: survey_raw["Azimuth"],
    }
)
# # Remove missing data
collar = collar.dropna(
    subset=[DhConfig.holeid, DhConfig.x, DhConfig.y, DhConfig.z, DhConfig.total_depth]
)
survey = survey.dropna(subset=[DhConfig.holeid, DhConfig.depth, DhConfig.dip, DhConfig.azimuth])
#
# # Create database
db = DrillholeDatabase(collar=collar, survey=survey)

###############################################################################
# Database Statistics
# -------------------
print("\nDatabase Statistics:")
print(f"Total holes: {len(db.list_holes())}")
print(f"Total collar records: {len(db.collar)}")
print(f"Total survey records: {len(db.survey)}")

# Show coordinate ranges
extent = db.extent()
print("\nCoordinate Ranges:")
print(f"X (Easting): {extent[0]:.1f} to {extent[1]:.1f}")
print(f"Y (Northing): {extent[2]:.1f} to {extent[3]:.1f}")
print(f"Z (Elevation): {extent[4]:.1f} to {extent[5]:.1f}")

###############################################################################
# Access Individual Drillholes
# ----------------------------
if len(db.list_holes()) > 0:
    # Get the first available hole
    first_hole_id = db.list_holes()[0]
    hole = db[first_hole_id]

    print(f"\nExample: Accessing hole '{first_hole_id}':")
    print(f"Total depth: {hole.collar[DhConfig.total_depth].iloc[0]:.1f}m")
    print(f"Number of survey points: {len(hole.survey)}")

###############################################################################
# Summary
# -------
print("\n" + "=" * 70)
print("Summary:")
print("  ✓ Used DrillholeDatabase.from_csv() to load drilling data")
print("  ✓ Specified column mapping for both collar and survey files")
print("  ✓ Database automatically validated and normalized the data")
print("  ✓ Ready to add interval/point tables or perform analysis")
print("=" * 70)
