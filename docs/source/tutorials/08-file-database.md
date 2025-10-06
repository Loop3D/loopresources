# File Database Backend for DrillholeDatabase — Tutorial

This short tutorial shows how to use the file-based (SQLite) backend for
`DrillholeDatabase`. It covers two common workflows:

- Creating a file-backed database from scratch (either by constructing directly
  or saving an in-memory database)
- Loading or linking to an existing SQLite database and working with projects
  and per-hole queries

Prerequisites

- Python environment with project requirements installed (see
  `requirements.txt`)
- `loopresources` package available in the environment (the workspace contains
  the package source)

Quick overview

- Memory backend (default) keeps tables in pandas DataFrames in RAM
- File backend stores tables in an SQLite file and fetches data on demand
- File backend supports multiple projects (optional `project_name`) in the same
  file
- DrillHole access is optimized for file backend: only data for the requested
  hole is loaded

1. Creating a file-backed database from scratch

Option A — Create directly with a file backend

```python
import pandas as pd
from loopresources.drillhole import DrillholeDatabase, DbConfig

# Prepare minimal sample data
collar = pd.DataFrame({"HOLEID": ["DH001", "DH002"], "EAST": [100.0, 200.0], "NORTH": [1000.0, 2000.0], "RL": [50.0, 60.0], "DEPTH": [100.0, 150.0]})

survey = pd.DataFrame({"HOLEID": ["DH001", "DH001", "DH002"], "DEPTH": [0.0, 50.0, 0.0], "AZIMUTH": [0.0, 0.0, 45.0], "DIP": [90.0, 90.0, 80.0]})

# Create a DbConfig that uses a file backend
config = DbConfig(backend="file", db_path="drillholes.db")

# Construct the DrillholeDatabase; data is persisted to the SQLite file
db = DrillholeDatabase(collar, survey, db_config=config)

# Inspect holes
print(db.list_holes())
```

Option B — Create in memory then save to file

```python
from loopresources.drillhole import DrillholeDatabase

# Create in-memory database (default)
db_mem = DrillholeDatabase(collar, survey)

# Save to SQLite file. Optionally set a project name.
db_mem.save_to_database("drillholes.db", project_name="Project_A")
```

Notes:

- Use `overwrite=True` in `save_to_database()` to replace an existing project
  with the same `project_name`.
- When saving without a `project_name`, tables are written without project
  scoping (useful for single-project files).

2. Loading or linking to an existing file database

The library provides two patterns for opening existing databases:

- `from_database(db_path, project_name=None)` — loads the project into memory
  (or creates a file-backed object that behaves like a full database instance)
- `link_to_database(db_path, project_name=None)` — creates a linked connection
  that fetches data on-demand; useful for very large datasets

Examples

```python
from loopresources.drillhole import DrillholeDatabase

# Load a project from file (loads into a DrillholeDatabase instance)
db_loaded = DrillholeDatabase.from_database("drillholes.db", project_name="Project_A")

# Or create a linked connection (data read on demand from disk)
db_linked = DrillholeDatabase.link_to_database("drillholes.db", project_name="Project_A")
```

Working with holes and optimized access

When using the file backend (either created directly or linked),
`DrillholeDatabase` and `DrillHole` will use optimized SQL queries so only the
rows for a single hole are returned when you access a specific hole:

```python
# Access a single DrillHole (only that hole's collar/survey/interval/point rows are queried)
dh = db_linked["DH001"]
print(dh.collar)  # collar rows for DH001 only
print(dh.survey)  # survey rows for DH001 only
```

If you need programmatic access to the optimized methods, the database exposes
helpers such as:

- `get_collar_for_hole(holeid)`
- `get_survey_for_hole(holeid)`
- `get_interval_data_for_hole(table_name, holeid)`
- `get_point_data_for_hole(table_name, holeid)`

(These names are exposed in the API; consult the package docs or code if you
need exact signatures.)

3. Multiple projects in one file

You can store multiple named projects inside a single SQLite file by providing
`project_name` when saving. Later you can load or link to a specific project
using the same name.

```python
# Save two separate projects into one file
db1.save_to_database("multi.db", project_name="Project_A")
db2.save_to_database("multi.db", project_name="Project_B")

# Load each project independently
db_a = DrillholeDatabase.from_database("multi.db", project_name="Project_A")
db_b = DrillholeDatabase.from_database("multi.db", project_name="Project_B")
```

4. Practical tips and troubleshooting

- Run the demo script to see full examples: `python demo_file_database.py`
- Run tests related to the file backend: `pytest tests/test_file_database.py -v`
- If a `project_name` already exists in the file and you want to replace it, use
  `overwrite=True` when saving
- Use SQLite browser tools to inspect the SQLite file if needed

Schema and behaviour notes

- The file backend creates a `projects` table plus tables for `collar`,
  `survey`, `interval_*`, and `point_*` tables
- Each table contains the original columns from the DataFrame and a `project_id`
  column when `project_name` is used
- Queries against a specific hole include `WHERE HOLEID = ?` so only relevant
  rows are loaded

Conclusion

The file backend provides a drop-in alternative to the in-memory backend when
persistence, memory efficiency, or sharing via SQLite is required. Use
`DbConfig(backend='file', db_path=...)` to create file-backed databases, or save
existing in-memory databases with `save_to_database()`. For large datasets
prefer `link_to_database()` to minimize memory use and rely on optimized
per-hole queries.

For more complete examples see `demo_file_database.py` and the API reference in
the project docs.
