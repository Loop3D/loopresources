# File Database Backend for DrillholeDatabase

This document describes the file-based database backend feature added to DrillholeDatabase, which allows storing drillhole data in SQLite databases instead of keeping everything in RAM.

## Features

- **Optional file-based storage**: Choose between in-memory (pandas) or file-based (SQLite) storage
- **Project organization**: Support multiple projects in a single database file
- **Persistence**: Save and load databases from disk
- **Memory efficiency**: Large datasets don't fill up RAM when using file backend
- **Backward compatible**: Default behavior remains unchanged (memory backend)

## Configuration

The `DbConfig` class controls database backend configuration:

```python
from loopresources.drillhole import DbConfig

# Memory backend (default)
config = DbConfig(backend='memory')

# File backend
config = DbConfig(backend='file', db_path='/path/to/database.db')

# File backend with project
config = DbConfig(backend='file', db_path='/path/to/database.db', project_name='MyProject')
```

### Parameters

- **backend** (str): Database backend type - 'memory' (default) or 'file'
- **db_path** (str): Path to SQLite database file (required if backend='file')
- **project_name** (str, optional): Name of the project to associate with this database

## Usage Examples

### Basic Usage - Memory Backend (Default)

```python
from loopresources.drillhole import DrillholeDatabase
import pandas as pd

# Create sample data
collar = pd.DataFrame({
    'HOLEID': ['DH001', 'DH002'],
    'EAST': [100.0, 200.0],
    'NORTH': [1000.0, 2000.0],
    'RL': [50.0, 60.0],
    'DEPTH': [100.0, 150.0]
})

survey = pd.DataFrame({
    'HOLEID': ['DH001', 'DH001', 'DH002'],
    'DEPTH': [0.0, 50.0, 0.0],
    'AZIMUTH': [0.0, 0.0, 45.0],
    'DIP': [90.0, 90.0, 80.0]
})

# Create database (defaults to memory backend)
db = DrillholeDatabase(collar, survey)
```

### File Backend

```python
from loopresources.drillhole import DrillholeDatabase, DbConfig

# Create database with file backend
db_config = DbConfig(backend='file', db_path='drillholes.db')
db = DrillholeDatabase(collar, survey, db_config)

# Data is automatically stored in SQLite database
# Access works the same way
print(db.list_holes())
```

### Save to Database

```python
# Create database in memory
db = DrillholeDatabase(collar, survey)

# Save to SQLite file
db.save_to_database('drillholes.db')

# Save with project name
db.save_to_database('drillholes.db', project_name='Project_A')

# Overwrite existing project
db.save_to_database('drillholes.db', project_name='Project_A', overwrite=True)
```

### Load from Database

```python
# Load entire database
db = DrillholeDatabase.from_database('drillholes.db')

# Load specific project
db = DrillholeDatabase.from_database('drillholes.db', project_name='Project_A')
```

### Link to Existing Database

```python
# Create a linked connection to database
db = DrillholeDatabase.link_to_database('drillholes.db', project_name='Project_A')

# Data is loaded on-demand from the database
print(db.list_holes())
```

### Multiple Projects in One Database

```python
# Save multiple projects to same database file
db1 = DrillholeDatabase(collar1, survey1)
db1.save_to_database('multi_project.db', project_name='Project_A')

db2 = DrillholeDatabase(collar2, survey2)
db2.save_to_database('multi_project.db', project_name='Project_B')

# Load each project separately
db_a = DrillholeDatabase.from_database('multi_project.db', project_name='Project_A')
db_b = DrillholeDatabase.from_database('multi_project.db', project_name='Project_B')
```

## Database Schema

When using file backend, the following tables are created:

### projects table
- `id`: INTEGER PRIMARY KEY
- `name`: TEXT UNIQUE
- `created_at`: TIMESTAMP
- `metadata`: TEXT

### collar table
- All columns from input DataFrame
- `project_id`: INTEGER (if project is specified)

### survey table
- All columns from input DataFrame
- `project_id`: INTEGER (if project is specified)

### interval_* tables
- One table per interval table added
- All columns from input DataFrame
- `project_id`: INTEGER (if project is specified)

### point_* tables
- One table per point table added
- All columns from input DataFrame
- `project_id`: INTEGER (if project is specified)

## When to Use File Backend

Use **file backend** when:
- Working with large datasets that may not fit in RAM
- Need persistent storage across sessions
- Want to share data with other tools that can read SQLite
- Managing multiple related projects

Use **memory backend** when:
- Dataset is small enough to fit comfortably in RAM
- Need maximum performance for computations
- Working with temporary or exploratory analyses

## API Reference

### DrillholeDatabase Constructor

```python
DrillholeDatabase(collar, survey, db_config=None)
```

**Parameters:**
- `collar` (pd.DataFrame): Collar data
- `survey` (pd.DataFrame): Survey data
- `db_config` (DbConfig, optional): Database configuration. Defaults to memory backend.

### Class Methods

#### from_database()
```python
DrillholeDatabase.from_database(db_path, project_name=None)
```

Load database from SQLite file.

**Parameters:**
- `db_path` (str): Path to SQLite database file
- `project_name` (str, optional): Project to load

**Returns:** DrillholeDatabase instance

#### link_to_database()
```python
DrillholeDatabase.link_to_database(db_path, project_name=None)
```

Create a linked connection to existing database.

**Parameters:**
- `db_path` (str): Path to SQLite database file
- `project_name` (str, optional): Project to link to

**Returns:** DrillholeDatabase instance

### Instance Methods

#### save_to_database()
```python
db.save_to_database(db_path, project_name=None, overwrite=False)
```

Save database to SQLite file.

**Parameters:**
- `db_path` (str): Path to SQLite database file
- `project_name` (str, optional): Project name to save as
- `overwrite` (bool): If True, overwrite existing project data

## Demo Script

See `demo_file_database.py` for a comprehensive demonstration of all features.

Run it with:
```bash
python demo_file_database.py
```

## Testing

Run the test suite:
```bash
pytest tests/test_file_database.py -v
```

## Notes

- The file backend is fully backward compatible - existing code continues to work unchanged
- Both backends support the same API for filtering, validation, and data access
- SQLite databases are portable and can be opened with standard SQLite tools
- Project organization allows multiple teams to work with separate datasets in a single database file
