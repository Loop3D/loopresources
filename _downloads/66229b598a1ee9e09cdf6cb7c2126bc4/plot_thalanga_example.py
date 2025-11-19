"""
Thalanga Drillhole Database Example
===================================

This example demonstrates how to load collar and survey data from the Thalanga dataset
and create a drillhole database using loopresources.
"""

import pandas as pd
import os
from loopresources.drillhole import DrillholeDatabase, DhConfig

###############################################################################
# Load Thalanga Data
# ------------------
# Load the collar and survey data from the CSV files in the thalanga folder.

# Get the path to the thalanga data folder
# Sphinx Gallery does not define __file__, so use a relative path
# This works both in Sphinx Gallery and when running as a script/notebook

data_folder = os.path.join(".", "thalanga")

# Load collar data
collar_file = os.path.join(data_folder, "ThalangaML_collar.csv")
collar_raw = pd.read_csv(collar_file)

print("Raw collar data columns:")
print(collar_raw.columns.tolist())
print(f"\nLoaded {len(collar_raw)} collar records")
print("First few records:")
print(collar_raw.head())

###############################################################################
# Load survey data
survey_file = os.path.join(data_folder, "ThalangaML_survey.csv")
survey_raw = pd.read_csv(survey_file)

print("\nRaw survey data columns:")
print(survey_raw.columns.tolist())
print(f"\nLoaded {len(survey_raw)} survey records")
print("First few records:")
print(survey_raw.head())

###############################################################################
# Prepare Data for loopresources
# -------------------------------
# Map the Thalanga column names to the expected loopresources column names.

# Prepare collar data - map columns to DhConfig expected names
collar = pd.DataFrame(
    {
        DhConfig.holeid: collar_raw["HOLE_ID"],
        DhConfig.x: collar_raw["X_MGA"],  # Easting
        DhConfig.y: collar_raw["Y_MGA"],  # Northing
        DhConfig.z: collar_raw["Z_MGA"],  # Elevation
        DhConfig.total_depth: collar_raw["DEPTH"],  # Total depth
    }
)

# Remove any rows with missing essential data
collar = collar.dropna(
    subset=[DhConfig.holeid, DhConfig.x, DhConfig.y, DhConfig.z, DhConfig.total_depth]
)

print("\nPrepared collar data:")
print(f"Shape: {collar.shape}")
print(collar.head())

###############################################################################
# Prepare survey data - map columns to DhConfig expected names
survey = pd.DataFrame(
    {
        DhConfig.holeid: survey_raw["Drillhole ID"],
        DhConfig.depth: survey_raw["Depth"],
        DhConfig.dip: survey_raw["Dip"],  # Dip in degrees
        DhConfig.azimuth: survey_raw["Azimuth"],  # Azimuth in degrees
    }
)

# Remove any rows with missing essential data
survey = survey.dropna(subset=[DhConfig.holeid, DhConfig.depth, DhConfig.dip, DhConfig.azimuth])

print("\nPrepared survey data:")
print(f"Shape: {survey.shape}")
print(survey.head())

###############################################################################
# Create DrillHole Database
# -------------------------
# Initialize the DrillholeDatabase with collar and survey data.

# Create the drillhole database
db = DrillholeDatabase(collar=collar, survey=survey)

print("\nCreated DrillHole Database!")
print(f"Number of holes: {len(db.list_holes())}")
print(f"Available holes: {db.list_holes()[:10]}...")  # Show first 10 holes

###############################################################################
# Explore the Database
# --------------------
# Demonstrate basic operations with the drillhole database.

print("\nDatabase Statistics:")
print(f"Total holes in collar data: {len(collar[DhConfig.holeid].unique())}")
print(f"Total holes in survey data: {len(survey[DhConfig.holeid].unique())}")
print(f"Total holes in database: {len(db.list_holes())}")

# Show coordinate ranges
print("\nCoordinate Ranges:")
print(f"X (Easting): {collar[DhConfig.x].min():.1f} to {collar[DhConfig.x].max():.1f}")
print(f"Y (Northing): {collar[DhConfig.y].min():.1f} to {collar[DhConfig.y].max():.1f}")
print(f"Z (Elevation): {collar[DhConfig.z].min():.1f} to {collar[DhConfig.z].max():.1f}")
print(
    f"Depth: {collar[DhConfig.total_depth].min():.1f} to {collar[DhConfig.total_depth].max():.1f}"
)

###############################################################################
# Access Individual Drillholes
# ----------------------------
# Demonstrate how to access individual drillhole data.

if len(db.list_holes()) > 0:
    # Get the first available hole
    holes = db.list_holes()
    first_hole_id = holes[0]
    hole = db[first_hole_id]

    print(f"\nExample: Accessing hole '{first_hole_id}':")
    print("Collar information:")
    print(hole.collar)

    print("\nSurvey information:")
    print(hole.survey)

    print("\nHole statistics:")
    print(f"Total depth: {hole.collar[DhConfig.total_depth].iloc[0]:.1f}m")
    print(f"Number of survey points: {len(hole.survey)}")

###############################################################################
# Summary
# -------
print("\nSummary:")
print("Successfully loaded Thalanga drillhole data into loopresources DrillholeDatabase")
print(f"The database contains {len(db.list_holes())} drillholes")
print("You can now access individual holes using: hole = db['HOLE_ID']")
print(
    "Next steps would be to load assay or geological data using add_interval_table() or add_point_table() methods"
)
