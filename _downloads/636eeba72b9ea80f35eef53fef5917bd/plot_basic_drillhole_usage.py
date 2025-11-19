"""
Basic DrillholeDatabase Usage
=============================

This example demonstrates the basic usage of the DrillholeDatabase class
for managing drillhole data with modern pandas-based operations.
"""

import pandas as pd
import matplotlib.pyplot as plt
from loopresources.drillhole.drillhole_database import DrillholeDatabase
from loopresources.drillhole.dhconfig import DhConfig

###############################################################################
# Creating Sample Data
# --------------------
# First, let's create some sample drillhole data to work with.

# Create collar data - one row per drillhole
collar = pd.DataFrame(
    {
        DhConfig.holeid: ["DH001", "DH002", "DH003", "DH004"],
        DhConfig.x: [100.0, 200.0, 300.0, 400.0],
        DhConfig.y: [1000.0, 2000.0, 3000.0, 4000.0],
        DhConfig.z: [50.0, 60.0, 70.0, 80.0],
        DhConfig.total_depth: [150.0, 200.0, 180.0, 220.0],
    }
)

print("Collar data:")
print(collar.head())

###############################################################################
# Create survey data - one row per survey station
survey = pd.DataFrame(
    {
        DhConfig.holeid: ["DH001", "DH001", "DH001", "DH002", "DH002", "DH003", "DH004"],
        DhConfig.depth: [0.0, 50.0, 100.0, 0.0, 100.0, 0.0, 0.0],
        DhConfig.azimuth: [0.0, 0.0, 0.0, 45.0, 45.0, 90.0, 135.0],
        DhConfig.dip: [-90.0, -90.0, -90.0, -85.0, -80.0, -90.0, -90.0],
    }
)

print("\nSurvey data:")
print(survey.head())

###############################################################################
# Initialize Database
# -------------------
# Create a DrillholeDatabase instance with collar and survey data.

db = DrillholeDatabase(collar, survey)
print(f"\nCreated database with {len(db.list_holes())} holes")
print(f"Holes: {db.list_holes()}")

###############################################################################
# Working with Individual Holes
# -----------------------------
# Access individual drillholes using dictionary-like syntax.

# Get a specific hole
hole = db["DH001"]
print(f"\nAccessing hole: {hole.hole_id}")
print(f"Collar info:\n{hole.collar}")
print(f"Survey info:\n{hole.survey}")

###############################################################################
# Adding Interval Data
# --------------------
# Add some geological interval data to the database.

# Create sample lithology data
lithology = pd.DataFrame(
    {
        DhConfig.holeid: ["DH001", "DH001", "DH002", "DH002", "DH003"],
        DhConfig.sample_from: [0.0, 50.0, 0.0, 80.0, 0.0],
        DhConfig.sample_to: [50.0, 150.0, 80.0, 200.0, 180.0],
        "LITHO": ["Granite", "Schist", "Sandstone", "Shale", "Limestone"],
    }
)

# Add to database
db.add_interval_table("lithology", lithology)
print(f"\nAdded lithology data with {len(lithology)} intervals")

###############################################################################
# Create sample assay data
assays = pd.DataFrame(
    {
        DhConfig.holeid: ["DH001", "DH001", "DH001", "DH002", "DH002"],
        DhConfig.sample_from: [0.0, 25.0, 75.0, 0.0, 100.0],
        DhConfig.sample_to: [25.0, 75.0, 125.0, 100.0, 200.0],
        "AU_ppm": [0.1, 2.5, 0.8, 0.05, 1.2],
        "CU_pct": [0.05, 0.3, 0.15, 0.02, 0.25],
    }
)

db.add_interval_table("assays", assays)
print(f"Added assay data with {len(assays)} samples")

###############################################################################
# Filtering and Querying
# ----------------------
# Demonstrate various filtering operations.

# Filter by bounding box
bbox_filtered = db.filter(bbox=(150, 350, 1500, 3500))
print(f"\nFiltered by bbox: {len(bbox_filtered.list_holes())} holes remaining")
print(f"Holes in bbox: {bbox_filtered.list_holes()}")

# Filter by expression (high gold grades)
high_grade = db.filter(expr="AU_ppm > 1.0")
print(f"\nFiltered by AU > 1.0 ppm: {len(high_grade.list_holes())} holes with data")

###############################################################################
# Accessing Filtered Data
# -----------------------
# Work with filtered data at the hole level.

if high_grade.list_holes():
    first_hole = high_grade[high_grade.list_holes()[0]]
    if "assays" in high_grade.intervals:
        hole_assays = first_hole["assays"]
        print(f"\nHigh-grade assays for {first_hole.hole_id}:")
        print(hole_assays[["AU_ppm", "CU_pct"]])

###############################################################################
# Visualization
# ------------
# Create a simple plot showing hole locations.

fig, ax = plt.subplots(figsize=(10, 8))

# Plot all holes
x_coords = collar[DhConfig.x]
y_coords = collar[DhConfig.y]
ax.scatter(x_coords, y_coords, c="blue", s=100, alpha=0.7, label="All Holes")

# Highlight filtered holes if any
if bbox_filtered.list_holes():
    filtered_collar = bbox_filtered.collar
    ax.scatter(
        filtered_collar[DhConfig.x],
        filtered_collar[DhConfig.y],
        c="red",
        s=150,
        alpha=0.8,
        label="Bbox Filtered",
    )

# Add hole labels
for idx, row in collar.iterrows():
    ax.annotate(
        row[DhConfig.holeid],
        (row[DhConfig.x], row[DhConfig.y]),
        xytext=(5, 5),
        textcoords="offset points",
        fontsize=10,
        alpha=0.8,
    )

ax.set_xlabel("X Coordinate")
ax.set_ylabel("Y Coordinate")
ax.set_title("Drillhole Locations")
ax.legend()
ax.grid(True, alpha=0.3)

plt.tight_layout()
plt.show()

###############################################################################
# Database Statistics
# ------------------
# Show some summary statistics.

extent = db.extent()
print("\nDatabase extent (xmin, xmax, ymin, ymax, zmin, zmax):")
print(extent)

print(
    f"\nTotal depth range: {collar[DhConfig.total_depth].min():.1f} to {collar[DhConfig.total_depth].max():.1f}m"
)

if "assays" in db.intervals:
    assay_data = db.intervals["assays"]
    print("\nAssay statistics:")
    print(f"  Gold (AU): {assay_data['AU_ppm'].min():.2f} to {assay_data['AU_ppm'].max():.2f} ppm")
    print(f"  Copper (CU): {assay_data['CU_pct'].min():.2f} to {assay_data['CU_pct'].max():.2f} %")
