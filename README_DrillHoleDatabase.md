# DrillHoleDatabase - Clean Implementation

A modern, clean implementation of the DrillHoleDatabase class following the AGENTS.md specifications.

## Features

- **Clean Architecture**: Follows AGENTS.md specifications with clear separation of concerns
- **Pandas-Native**: Built on pandas DataFrames for efficient data manipulation
- **Filtering API**: Powerful filtering by holes, bounding box, depth range, and expressions
- **Preprocessing Tools**: Validate numerical data and filter by data quality thresholds
- **Validation**: Comprehensive validation of data integrity
- **Type Hints**: Full type annotations for better IDE support
- **Comprehensive Tests**: Extensive test suite using pytest
- **File Backend**: Optional SQLite storage for large datasets (see [File Database Backend](README_FileDatabase.md))

## Database Backend Options

### Memory Backend (Default)
Data is stored in pandas DataFrames in RAM - fast but limited by available memory.

### File Backend (New!)
Data is stored in SQLite database files - supports massive datasets and persistent storage.

```python
from loopresources.drillhole import DrillholeDatabase, DbConfig

# File backend with project organization
db_config = DbConfig(backend='file', db_path='drillholes.db', project_name='MyProject')
db = DrillholeDatabase(collar, survey, db_config)
```

See [README_FileDatabase.md](README_FileDatabase.md) for complete documentation.

## Quick Start

```python
import pandas as pd
from loopresources.drillhole import DrillholeDatabase

# Create collar data
collar = pd.DataFrame({
    'HOLEID': ['DH001', 'DH002', 'DH003'],
    'EAST': [100.0, 200.0, 300.0],
    'NORTH': [1000.0, 2000.0, 3000.0],
    'RL': [50.0, 60.0, 70.0],
    'DEPTH': [100.0, 150.0, 200.0]
})

# Create survey data
survey = pd.DataFrame({
    'HOLEID': ['DH001', 'DH001', 'DH002', 'DH002', 'DH003'],
    'DEPTH': [0.0, 50.0, 0.0, 75.0, 0.0],
    'AZIMUTH': [0.0, 0.0, 45.0, 45.0, 90.0],
    'DIP': [90.0, 90.0, 80.0, 80.0, 85.0]
})

# Initialize database
db = DrillholeDatabase(collar, survey)

# Add interval data
geology = pd.DataFrame({
    'HOLEID': ['DH001', 'DH001', 'DH002'],
    'SAMPFROM': [0.0, 30.0, 0.0],
    'SAMPTO': [30.0, 80.0, 100.0],
    'LITHO': ['granite', 'schist', 'granite']
})
db.add_interval_table('geology', geology)

# Add point data
assay = pd.DataFrame({
    'HOLEID': ['DH001', 'DH002'],
    'DEPTH': [10.0, 50.0],
    'CU_PPM': [500.0, 800.0]
})
db.add_point_table('assay', assay)
```

## Core Methods

### Database Operations

```python
# List all holes
holes = db.list_holes()  # ['DH001', 'DH002', 'DH003']

# Get spatial extent
xmin, xmax, ymin, ymax, zmin, zmax = db.extent()

# Validate data integrity
db.validate()
```

### Individual Hole Access

```python
# Get a single hole view
hole = db['DH001']

# Access hole data
collar_data = hole.collar
survey_data = hole.survey
geology_data = hole['geology']
assay_data = hole['assay']

# Get all tables
interval_tables = hole.interval_tables()
point_tables = hole.point_tables()

# Generate trace
trace = hole.trace(step=1.0)

# Find depth at XYZ coordinate
depth = hole.depth_at(x=105.0, y=1005.0, z=55.0)
```

### Filtering

```python
# Filter by specific holes
subset = db.filter(holes=['DH001', 'DH002'])

# Filter by bounding box
subset = db.filter(bbox=(50.0, 250.0, 500.0, 2500.0))

# Filter by depth range
subset = db.filter(depth_range=(0.0, 100.0))

# Filter by expression
subset = db.filter(expr="LITHO == 'granite'")

# Combined filtering
subset = db.filter(
    holes=['DH001', 'DH002'],
    depth_range=(0.0, 80.0),
    expr="CU_PPM > 400"
)
```

### Preprocessing and Data Quality

The database provides tools for validating and cleaning numerical data:

```python
# Validate numerical columns (converts strings, removes negatives/zeros)
db.validate_numerical_columns(
    'assay',
    columns=['CU_PPM', 'AU_PPM', 'AG_PPM'],
    allow_negative=False  # Replace values <= 0 with NaN
)

# Filter by data quality (remove rows with too many NaN values)
filtered_db = db.filter_by_nan_threshold(
    'assay',
    columns=['CU_PPM', 'AU_PPM', 'AG_PPM'],
    threshold=0.75  # Keep rows with ≥75% valid values
)

# Chain preprocessing operations
clean_db = (db
    .validate_numerical_columns('assay', ['CU_PPM', 'AU_PPM'], allow_negative=False)
    .filter(holes=['DH001', 'DH002'])
    .filter_by_nan_threshold('assay', ['CU_PPM', 'AU_PPM'], threshold=0.8)
)
```

See `examples/example_preprocessing.py` for a complete example.

## Data Model

The DrillHoleDatabase follows a two-tiered data model:

1. **DrillholeDatabase** - Main container for all drillhole data
2. **DrillHole** - Per-hole view providing convenient access

### Required Columns

**Collar:**
- HOLEID, EAST, NORTH, RL, DEPTH

**Survey:**
- HOLEID, DEPTH, AZIMUTH, DIP

**Interval Tables:**
- HOLEID, SAMPFROM, SAMPTO

**Point Tables:**
- HOLEID, DEPTH

## Validation

The database automatically validates:
- All required columns are present
- No duplicate HOLE_IDs in collar
- All survey/interval/point holes exist in collar
- Depths don't exceed total depth
- Angles are converted from degrees to radians if needed

## Testing

Run the comprehensive test suite:

```bash
pytest tests/test_drillhole_database*.py -v
```

## Example Workflow

See `demo_drillhole_database.py` for a complete example demonstrating all features.

## Comparison with Existing DrillHoleDB

The new DrillHoleDatabase provides:

- ✅ Cleaner API following AGENTS.md specifications
- ✅ Better type hints and documentation
- ✅ More robust filtering capabilities
- ✅ Comprehensive validation
- ✅ Extensive test coverage
- ✅ Pandas-native design
- ✅ Error handling for edge cases

While maintaining compatibility with existing DhConfig and utility functions.