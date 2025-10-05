# String Representation Methods - Implementation Summary

## Overview

This implementation adds comprehensive `__str__` and `__repr__` methods to the `DrillHole`, `DrillholeDatabase`, and `DhConfig` classes to provide rich, informative string representations for drillhole analysis and management in Python.

## Changes Made

### 1. DrillHole Class

Added two new methods to `/loopresources/drillhole/drillhole_database.py`:

#### `__repr__(self) -> str`
- Returns a concise single-line representation
- Format: `DrillHole(hole_id='DH001', depth=150.00m)`
- Useful for debugging and quick identification

#### `__str__(self) -> str`
- Returns a detailed multi-line representation including:
  - Hole ID and location (X, Y, Z coordinates)
  - Total depth
  - Average azimuth and dip (automatically converted from radians to degrees for readability)
  - List of attached interval tables with:
    - Number of intervals
    - Statistics for numerical columns (mean, min, max, count)
    - Unique value counts for categorical columns
  - List of attached point tables with similar statistics
- Handles NaN values gracefully
- Shows helpful "None" message when no tables are attached

**Example Output:**
```
DrillHole: DH001
================
Location: X=100.00, Y=1000.00, Z=50.00
Total Depth: 150.00m
Average Azimuth: 5.00°
Average Dip: 87.67°

Interval Tables (2):
  - geology: 3 intervals
    • LITHO: 2 unique values (n=3)
  - assay: 3 intervals
    • CU_PPM: mean=666.67, min=300.00, max=1200.00 (n=3)
    • AU_PPM: mean=0.67, min=0.30, max=1.20 (n=3)
    • DENSITY: mean=2.70, min=2.60, max=2.80 (n=3)

Point Tables: None
```

### 2. DrillholeDatabase Class

Added two new methods to `/loopresources/drillhole/drillhole_database.py`:

#### `__repr__(self) -> str`
- Returns a concise single-line representation
- Format: `DrillholeDatabase(holes=5, interval_tables=2, point_tables=1)`
- Useful for quick overview

#### `__str__(self) -> str`
- Returns a detailed multi-line representation including:
  - Number of drillholes
  - Spatial extent (X, Y, Z ranges)
  - List of interval tables with:
    - Row counts
    - Column names (excluding standard columns)
    - Number of holes with data
  - List of point tables with similar information

**Example Output:**
```
DrillholeDatabase
=================
Number of Drillholes: 5
Spatial Extent:
  X: 100.00 to 500.00 (range: 400.00)
  Y: 1000.00 to 5000.00 (range: 4000.00)
  Z: 50.00 to 90.00 (range: 40.00)

Interval Tables (2):
  - geology:
    Rows: 9
    Columns: LITHO
    Holes with data: 5/5
  - assay:
    Rows: 9
    Columns: CU_PPM, AU_PPM, DENSITY
    Holes with data: 5/5

Point Tables (1):
  - structure:
    Rows: 4
    Columns: STRUCTURE_TYPE, ORIENTATION
    Holes with data: 4/5
```

### 3. DhConfig Class

Added `__str__` method to `/loopresources/drillhole/dhconfig.py`:

#### `__str__(self) -> str`
- Returns a formatted display of all column mappings
- Shows field names and their corresponding column names
- Includes boolean configuration flags
- Note: `__repr__` method already existed

**Example Output:**
```
DhConfig - Column Mapping
==========================
Hole ID:         HOLEID
Sample From:     SAMPFROM
Sample To:       SAMPTO
X Coordinate:    EAST
Y Coordinate:    NORTH
Z Coordinate:    RL
Azimuth:         AZIMUTH
Dip:             DIP
Depth:           DEPTH
Total Depth:     DEPTH
Add 90°:         True
Positive Dips Down: True
Dip is Inclination: False
```

## Test Coverage

Created comprehensive test suite in `/tests/test_str_repr.py`:

- **16 test cases** covering:
  - DhConfig string representations
  - DrillholeDatabase repr and str methods
  - DrillHole repr and str methods
  - Edge cases (empty tables, NaN values, point tables)
  - Format validation (concise repr, detailed str)
  - Content validation (key information present)

- **All tests passing** (47 total passed, 1 skipped)
- **No breaking changes** to existing functionality

## Design Decisions

1. **Angle Display**: Angles are automatically converted from radians to degrees in the display, making them more intuitive for users while maintaining internal consistency.

2. **Statistics**: For numerical columns, show mean, min, max, and non-null count. For categorical columns, show unique value counts.

3. **Concise vs Detailed**: `__repr__` provides single-line concise output suitable for debugging, while `__str__` provides detailed multi-line output for human reading.

4. **Graceful Handling**: Both methods handle edge cases gracefully:
   - Empty tables show "None"
   - NaN values are counted and reported
   - Missing data doesn't cause errors

5. **Jupyter Notebook Friendly**: The output is formatted to be easily readable in Jupyter notebooks and interactive Python sessions.

## Usage Examples

### Quick Overview
```python
>>> db = DrillholeDatabase.from_csv('collar.csv', 'survey.csv')
>>> db
DrillholeDatabase(holes=5, interval_tables=2, point_tables=1)

>>> print(db)  # Detailed view
DrillholeDatabase
=================
Number of Drillholes: 5
...
```

### Individual Hole Analysis
```python
>>> hole = db['DH001']
>>> hole
DrillHole(hole_id='DH001', depth=150.00m)

>>> print(hole)  # Detailed view with statistics
DrillHole: DH001
================
Location: X=100.00, Y=1000.00, Z=50.00
...
```

### Iteration and Quick Summary
```python
>>> for hole in db:
...     print(repr(hole))
DrillHole(hole_id='DH001', depth=150.00m)
DrillHole(hole_id='DH002', depth=200.00m)
DrillHole(hole_id='DH003', depth=180.00m)
...
```

### Configuration Display
```python
>>> config = DhConfig()
>>> print(config)
DhConfig - Column Mapping
==========================
Hole ID:         HOLEID
...
```

## Benefits

1. **Interactive Development**: Easy exploration of drillhole data in Python REPL or Jupyter notebooks
2. **Quick Diagnostics**: Rapidly understand data structure and content
3. **Data Quality Assessment**: Immediate visibility into missing data and statistics
4. **User-Friendly**: No need to remember specific method names to see key information
5. **Debugging**: Clear, informative output when inspecting objects

## Files Modified

1. `/loopresources/drillhole/drillhole_database.py` - Added `__str__` and `__repr__` to DrillHole and DrillholeDatabase classes
2. `/loopresources/drillhole/dhconfig.py` - Added `__str__` to DhConfig class
3. `/tests/test_str_repr.py` - New comprehensive test file

## Backward Compatibility

- No breaking changes
- All existing tests continue to pass
- Methods are purely additive (adding new behavior, not changing existing)
- Existing code continues to work exactly as before
