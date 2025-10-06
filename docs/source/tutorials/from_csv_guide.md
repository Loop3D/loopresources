# DrillholeDatabase.from_csv() - Quick Start Guide

## Overview

The `from_csv()` class method provides a convenient way to load drilling data
directly from CSV files into a `DrillholeDatabase` object. It automatically
handles column mapping, data validation, and missing value removal.

## Basic Usage

### With Column Mapping

When your CSV files have different column names than what DrillholeDatabase
expects, use the column mapping feature:

```python
from loopresources.drillhole import DrillholeDatabase

db = DrillholeDatabase.from_csv(
    collar_file="path/to/collar.csv",
    survey_file="path/to/survey.csv",
    collar_columns={
        "holeid": "HOLE_ID",  # Map CSV column 'HOLE_ID' to holeid
        "x": "X_MGA",  # Map CSV column 'X_MGA' to x coordinate
        "y": "Y_MGA",  # Map CSV column 'Y_MGA' to y coordinate
        "z": "Z_MGA",  # Map CSV column 'Z_MGA' to z coordinate
        "total_depth": "DEPTH",  # Map CSV column 'DEPTH' to total_depth
    },
    survey_columns={
        "holeid": "Drillhole ID",  # Map CSV column 'Drillhole ID' to holeid
        "depth": "Depth",  # Map CSV column 'Depth' to depth
        "azimuth": "Azimuth",  # Map CSV column 'Azimuth' to azimuth
        "dip": "Dip",  # Map CSV column 'Dip' to dip
    },
)
```

### Without Column Mapping

If your CSV columns already match the DhConfig names, you can load them
directly:

```python
db = DrillholeDatabase.from_csv(collar_file="collar.csv", survey_file="survey.csv")
```

## Required Columns

### Collar CSV Requirements

- **holeid**: Unique identifier for each drillhole
- **x**: X coordinate (easting)
- **y**: Y coordinate (northing)
- **z**: Z coordinate (elevation)
- **total_depth**: Total depth of the drillhole

### Survey CSV Requirements

- **holeid**: Unique identifier matching collar data
- **depth**: Depth along hole
- **azimuth**: Azimuth angle (automatically converted from degrees if needed)
- **dip**: Dip angle (automatically converted from degrees if needed)

## Features

### Automatic Data Cleaning

- Removes rows with missing essential data
- No manual `dropna()` calls needed

### Angle Normalization

- Automatically detects if angles are in degrees
- Converts to radians if necessary

### Column Preservation

- Extra columns not in the mapping are preserved
- Useful for maintaining metadata

### Data Validation

- Validates required columns exist
- Checks for duplicate hole IDs
- Ensures survey holes exist in collar data

## Advanced Options

### Passing pandas read_csv Options

You can pass additional parameters to `pd.read_csv()`:

```python
db = DrillholeDatabase.from_csv(
    collar_file="collar.csv",
    survey_file="survey.csv",
    collar_columns={...},
    survey_columns={...},
    # pandas read_csv parameters
    encoding="utf-8",
    sep=",",
    skiprows=1,
)
```

## Complete Example

```python
from loopresources.drillhole import DrillholeDatabase, DhConfig

# Load data with column mapping
db = DrillholeDatabase.from_csv(
    collar_file="ThalangaML_collar.csv",
    survey_file="ThalangaML_survey.csv",
    collar_columns={"holeid": "HOLE_ID", "x": "X_MGA", "y": "Y_MGA", "z": "Z_MGA", "total_depth": "DEPTH"},
    survey_columns={"holeid": "Drillhole ID", "depth": "Depth", "azimuth": "Azimuth", "dip": "Dip"},
)

# Use the database
print(f"Loaded {len(db.list_holes())} drillholes")
print(f"Extent: {db.extent()}")

# Access individual holes
hole = db["DH001"]
print(f"Total depth: {hole.collar[DhConfig.total_depth].iloc[0]}")
```

## Benefits Over Manual Loading

**Before (manual loading):**

```python
import pandas as pd

# Load CSV files
collar_raw = pd.read_csv("collar.csv")
survey_raw = pd.read_csv("survey.csv")

# Manually map columns
collar = pd.DataFrame(
    {
        DhConfig.holeid: collar_raw["HOLE_ID"],
        DhConfig.x: collar_raw["X_MGA"],
        DhConfig.y: collar_raw["Y_MGA"],
        DhConfig.z: collar_raw["Z_MGA"],
        DhConfig.total_depth: collar_raw["DEPTH"],
    }
)

survey = pd.DataFrame(
    {
        DhConfig.holeid: survey_raw["Drillhole ID"],
        DhConfig.depth: survey_raw["Depth"],
        DhConfig.dip: survey_raw["Dip"],
        DhConfig.azimuth: survey_raw["Azimuth"],
    }
)

# Remove missing data
collar = collar.dropna(subset=[DhConfig.holeid, DhConfig.x, DhConfig.y, DhConfig.z, DhConfig.total_depth])
survey = survey.dropna(subset=[DhConfig.holeid, DhConfig.depth, DhConfig.dip, DhConfig.azimuth])

# Create database
db = DrillholeDatabase(collar=collar, survey=survey)
```

**After (using from_csv):**

```python
db = DrillholeDatabase.from_csv(
    collar_file="collar.csv",
    survey_file="survey.csv",
    collar_columns={"holeid": "HOLE_ID", "x": "X_MGA", "y": "Y_MGA", "z": "Z_MGA", "total_depth": "DEPTH"},
    survey_columns={"holeid": "Drillhole ID", "depth": "Depth", "azimuth": "Azimuth", "dip": "Dip"},
)
```

## Error Handling

The method will raise clear error messages for common issues:

- **Missing column in CSV**:
  `ValueError: Column 'INVALID_COLUMN' specified in collar_columns mapping not found`
- **Missing required columns after mapping**:
  `ValueError: Missing required collar columns: ['HOLEID', 'EAST']`
- **Duplicate hole IDs**: `ValueError: Duplicate HOLE_IDs found in collar data`
- **Survey holes not in collar**:
  `ValueError: Survey holes not found in collar: {'DH999'}`

## See Also

- `examples/plot_from_csv_example.py` - Complete working example with Thalanga
  data
- `examples/plot_thalanga_example.py` - Original manual loading example
- `tests/test_from_csv.py` - Comprehensive test suite
