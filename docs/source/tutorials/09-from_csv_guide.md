# 9 - `DrillholeDatabase.from_csv()` – Quick Start Guide

## 📘 Overview

The `from_csv()` class method provides a convenient way to load drilling data
directly from CSV files into a `DrillholeDatabase` object. It automatically
handles:

- Column mapping
- Data validation
- Missing value removal

---

## 🚀 Basic Usage

### ✅ With Column Mapping

Use column mapping when your CSV files have different column names than
expected:

```python
from loopresources.drillhole import DrillholeDatabase

db = DrillholeDatabase.from_csv(
    collar_file="path/to/collar.csv",
    survey_file="path/to/survey.csv",
    collar_columns={
        "holeid": "HOLE_ID",
        "x": "X_MGA",
        "y": "Y_MGA",
        "z": "Z_MGA",
        "total_depth": "DEPTH",
    },
    survey_columns={
        "holeid": "Drillhole ID",
        "depth": "Depth",
        "azimuth": "Azimuth",
        "dip": "Dip",
    },
)
```

### 🔄 Without Column Mapping

If your CSV columns already match `DhConfig` names:

```python
db = DrillholeDatabase.from_csv(collar_file="collar.csv", survey_file="survey.csv")
```

---

## 📋 Required Columns

### 📍 Collar CSV

- `holeid`: Unique drillhole ID
- `x`: Easting
- `y`: Northing
- `z`: Elevation
- `total_depth`: Total depth

### 📍 Survey CSV

- `holeid`: Must match collar data
- `depth`: Along-hole depth
- `azimuth`: Azimuth angle
- `dip`: Dip angle

---

## ✨ Features

### 🧼 Automatic Data Cleaning

- Removes rows with missing essential data
- No need for manual `dropna()`

### 📐 Angle Normalization

- Detects angle units
- Converts to radians if needed

### 📦 Column Preservation

- Extra columns are retained
- Useful for metadata

### ✅ Data Validation

- Checks required columns
- Detects duplicate hole IDs
- Ensures survey holes exist in collar data

---

## ⚙️ Advanced Options

You can pass additional `pandas.read_csv()` parameters:

```python
db = DrillholeDatabase.from_csv(
    collar_file="collar.csv",
    survey_file="survey.csv",
    collar_columns={...},
    survey_columns={...},
    encoding="utf-8",
    sep=",",
    skiprows=1,
)
```

---

## 🧪 Complete Example

```python
from loopresources.drillhole import DrillholeDatabase, DhConfig

db = DrillholeDatabase.from_csv(
    collar_file="ThalangaML_collar.csv",
    survey_file="ThalangaML_survey.csv",
    collar_columns={"holeid": "HOLE_ID", "x": "X_MGA", "y": "Y_MGA", "z": "Z_MGA", "total_depth": "DEPTH"},
    survey_columns={"holeid": "Drillhole ID", "depth": "Depth", "azimuth": "Azimuth", "dip": "Dip"},
)

print(f"Loaded {len(db.list_holes())} drillholes")
print(f"Extent: {db.extent()}")

hole = db["DH001"]
print(f"Total depth: {hole.collar[DhConfig.total_depth].iloc[0]}")
```

---

## 🔄 Benefits Over Manual Loading

### ❌ Manual Loading

```python
import pandas as pd

collar_raw = pd.read_csv("collar.csv")
survey_raw = pd.read_csv("survey.csv")

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

collar = collar.dropna(subset=[DhConfig.holeid, DhConfig.x, DhConfig.y, DhConfig.z, DhConfig.total_depth])
survey = survey.dropna(subset=[DhConfig.holeid, DhConfig.depth, DhConfig.dip, DhConfig.azimuth])

db = DrillholeDatabase(collar=collar, survey=survey)
```

### ✅ Using `from_csv`

```python
db = DrillholeDatabase.from_csv(
    collar_file="collar.csv",
    survey_file="survey.csv",
    collar_columns={"holeid": "HOLE_ID", "x": "X_MGA", "y": "Y_MGA", "z": "Z_MGA", "total_depth": "DEPTH"},
    survey_columns={"holeid": "Drillhole ID", "depth": "Depth", "azimuth": "Azimuth", "dip": "Dip"},
)
```

---

## 🛑 Error Handling

Common error messages:

- **Missing column**:
  `ValueError: Column 'INVALID_COLUMN' specified in collar_columns mapping not found`

- **Missing required columns**:
  `ValueError: Missing required collar columns: ['HOLEID', 'EAST']`

- **Duplicate hole IDs**: `ValueError: Duplicate HOLE_IDs found in collar data`

- **Survey holes not in collar**:
  `ValueError: Survey holes not found in collar: {'DH999'}`

---

## 📁 See Also

- `examples/plot_from_csv_example.py` — Thalanga data loading example
- `examples/plot_thalanga_example.py` — Manual loading example
- `tests/test_from_csv.py` — Comprehensive test suite
