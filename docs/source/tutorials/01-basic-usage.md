# 1 — Basic Usage

This lesson shows how to load collar and survey CSV files into a
`DrillholeDatabase`.

### When columns match DhConfig names

```python
from loopresources.drillhole import DrillholeDatabase

db = DrillholeDatabase.from_csv(collar_file="collar.csv", survey_file="survey.csv")
```

### When you need to map columns

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

Notes:

- Extra columns are preserved.
- Required columns must be present after mapping.
