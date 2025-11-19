"""
Example demonstrating preprocessing and imputation tools for DrillholeDatabase.

This example shows how to:
1. Validate numerical columns in assay data
2. Filter rows based on NaN thresholds
3. Chain preprocessing operations
"""

import pandas as pd
import numpy as np
from loopresources.drillhole.drillhole_database import DrillholeDatabase
from loopresources.drillhole.dhconfig import DhConfig

###############################################################################
# Create Sample Data
# ------------------
# Create synthetic drillhole data with some quality issues

print("=" * 70)
print("Preprocessing and Imputation Tools - Example")
print("=" * 70)

# Collar data
collar = pd.DataFrame(
    {
        DhConfig.holeid: ["DH001", "DH002", "DH003"],
        DhConfig.x: [100.0, 200.0, 300.0],
        DhConfig.y: [1000.0, 2000.0, 3000.0],
        DhConfig.z: [50.0, 60.0, 70.0],
        DhConfig.total_depth: [100.0, 150.0, 200.0],
    }
)

# Survey data
survey = pd.DataFrame(
    {
        DhConfig.holeid: ["DH001", "DH001", "DH002", "DH002", "DH003"],
        DhConfig.depth: [0.0, 50.0, 0.0, 75.0, 0.0],
        DhConfig.azimuth: [0.0, 0.0, 45.0, 45.0, 90.0],
        DhConfig.dip: [90.0, 90.0, 80.0, 80.0, 85.0],
    }
)

# Assay data with quality issues:
# - Mixed data types (strings that should be numbers)
# - Negative values (which may be data errors)
# - Zero values (which may indicate below detection limit)
# - Missing values (NaN)
assay = pd.DataFrame(
    {
        DhConfig.holeid: ["DH001", "DH001", "DH001", "DH002", "DH002", "DH003", "DH003"],
        DhConfig.depth: [10.0, 25.0, 40.0, 50.0, 80.0, 100.0, 150.0],
        "CU_PPM": [
            500.0,
            "invalid",
            -100.0,
            0.0,
            1200.0,
            800.0,
            650.0,
        ],  # Mixed types, negative, zero
        "AU_PPM": [0.5, 1.2, 0.8, "N/A", 1.5, -0.1, 0.9],  # String and negative
        "AG_PPM": [10.0, 20.0, np.nan, np.nan, 15.0, 25.0, np.nan],  # Missing values
        "PB_PPM": [5.0, np.nan, np.nan, np.nan, 8.0, 12.0, 10.0],  # Sparse data
    }
)

print("\nOriginal Assay Data:")
print(assay.to_string(index=False))
print(f"\nTotal records: {len(assay)}")

###############################################################################
# Initialize Database
# -------------------

db = DrillholeDatabase(collar, survey)
db.add_point_table("assay", assay)

###############################################################################
# Step 1: Validate Numerical Columns
# -----------------------------------
# Clean the data by:
# - Converting strings to numbers (invalid values become NaN)
# - Replacing negative and zero values with NaN (allow_negative=False)

print("\n" + "=" * 70)
print("Step 1: Validate Numerical Columns")
print("=" * 70)

db.validate_numerical_columns(
    "assay",
    columns=["CU_PPM", "AU_PPM", "AG_PPM", "PB_PPM"],
    allow_negative=False,  # Replace values <= 0 with NaN
)

print("\nAfter validation (strings and non-positive values replaced with NaN):")
print(db.points["assay"].to_string(index=False))

# Count NaN values per column
nan_counts = db.points["assay"][["CU_PPM", "AU_PPM", "AG_PPM", "PB_PPM"]].isna().sum()
print("\nNaN count per column:")
print(nan_counts)

###############################################################################
# Step 2: Filter by NaN Threshold
# --------------------------------
# Remove records where too many assay values are missing

print("\n" + "=" * 70)
print("Step 2: Filter by NaN Threshold")
print("=" * 70)

# Keep only records where at least 75% of assay columns have valid values
filtered_db = db.filter_by_nan_threshold(
    "assay",
    columns=["CU_PPM", "AU_PPM", "AG_PPM", "PB_PPM"],
    threshold=0.75,  # At least 3 out of 4 columns must have valid data
)

print("\nAfter filtering (kept records with ≥75% valid values):")
print(filtered_db.points["assay"].to_string(index=False))
print(f"\nRecords remaining: {len(filtered_db.points['assay'])} / {len(assay)}")

###############################################################################
# Step 3: Combined Workflow with Chaining
# ----------------------------------------
# Demonstrate chaining preprocessing with spatial filtering

print("\n" + "=" * 70)
print("Step 3: Combined Workflow with Chaining")
print("=" * 70)

# Reset database
db = DrillholeDatabase(collar, survey)
db.add_point_table("assay", assay.copy())

# Chain operations:
# 1. Validate numerical columns
# 2. Filter spatially by holes
# 3. Filter by NaN threshold
result_db = (
    db.validate_numerical_columns("assay", ["CU_PPM", "AU_PPM", "AG_PPM"], allow_negative=False)
    .filter(holes=["DH001", "DH002"])  # Only keep specific holes
    .filter_by_nan_threshold("assay", ["CU_PPM", "AU_PPM", "AG_PPM"], threshold=0.67)
)

print("\nAfter chained operations:")
print("  1. Validated numerical columns")
print("  2. Filtered to holes: DH001, DH002")
print("  3. Filtered to records with ≥67% valid values")
print(f"\nHoles remaining: {result_db.list_holes()}")
print(f"Records remaining: {len(result_db.points['assay'])} / {len(assay)}")
print("\nFinal assay data:")
print(
    result_db.points["assay"][["HOLEID", "DEPTH", "CU_PPM", "AU_PPM", "AG_PPM"]].to_string(
        index=False
    )
)

###############################################################################
# Summary Statistics
# ------------------

print("\n" + "=" * 70)
print("Summary")
print("=" * 70)

print(f"\nOriginal data: {len(assay)} records across {len(collar)} holes")
print(
    f"After preprocessing: {len(result_db.points['assay'])} records across {len(result_db.list_holes())} holes"
)
print(f"Data retention: {len(result_db.points['assay']) / len(assay) * 100:.1f}%")

print("\nPreprocessing workflow successfully completed!")
print("=" * 70)
