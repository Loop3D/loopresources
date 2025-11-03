# 8 - File Database Backend for `DrillholeDatabase` — Tutorial

This tutorial demonstrates how to use the **file-based (SQLite) backend** for
`DrillholeDatabase`. It covers two common workflows:

- Creating a file-backed database from scratch
- Loading or linking to an existing SQLite database for project-based and
  per-hole queries

---

## 📋 Prerequisites

- Python environment with dependencies installed (`requirements.txt`)
- `loopresources` package available in your environment

---

## ⚡ Quick Overview

- **Memory backend** (default): stores tables in RAM using pandas DataFrames
- **File backend**: stores tables in an SQLite file and fetches data on demand
- Supports **multiple projects** via optional `project_name`
- Per-hole access is optimized: only relevant rows are loaded

---

## 1️⃣ Creating a File-Backed Database

### Option A — Create Directly with File Backend

```python
import pandas as pd
from loopresources.drillhole import DrillholeDatabase, DbConfig

collar = pd.DataFrame({"HOLEID": ["DH001", "DH002"], "EAST": [100.0, 200.0], "NORTH": [1000.0, 2000.0], "RL": [50.0, 60.0], "DEPTH": [100.0, 150.0]})

survey = pd.DataFrame({"HOLEID": ["DH001", "DH001", "DH002"], "DEPTH": [0.0, 50.0, 0.0], "AZIMUTH": [0.0, 0.0, 45.0], "DIP": [90.0, 90.0, 80.0]})

config = DbConfig(backend="file", db_path="drillholes.db")
db = DrillholeDatabase(collar, survey, db_config=config)

print(db.list_holes())
```

### Option B — Create In-Memory Then Save to File

```python
from loopresources.drillhole import DrillholeDatabase

db_mem = DrillholeDatabase(collar, survey)
db_mem.save_to_database("drillholes.db", project_name="Project_A")
```

**Notes**:

- Use `overwrite=True` to replace an existing project
- Omitting `project_name` saves tables without project scoping

---

## 2️⃣ Loading or Linking to an Existing File Database

### Load or Link Patterns

- `from_database(db_path, project_name=None)` — loads project into memory
- `link_to_database(db_path, project_name=None)` — creates a linked connection
  (on-demand access)

### Examples

```python
from loopresources.drillhole import DrillholeDatabase

db_loaded = DrillholeDatabase.from_database("drillholes.db", project_name="Project_A")
db_linked = DrillholeDatabase.link_to_database("drillholes.db", project_name="Project_A")
```

---

## 🔍 Working with Holes (Optimized Access)

```python
dh = db_linked["DH001"]
print(dh.collar)  # Only DH001 collar rows
print(dh.survey)  # Only DH001 survey rows
```

### Programmatic Access Helpers

- `get_collar_for_hole(holeid)`
- `get_survey_for_hole(holeid)`
- `get_interval_data_for_hole(table_name, holeid)`
- `get_point_data_for_hole(table_name, holeid)`

---

## 3️⃣ Multiple Projects in One File

```python
db1.save_to_database("multi.db", project_name="Project_A")
db2.save_to_database("multi.db", project_name="Project_B")

db_a = DrillholeDatabase.from_database("multi.db", project_name="Project_A")
db_b = DrillholeDatabase.from_database("multi.db", project_name="Project_B")
```

---

## 🛠️ Practical Tips & Troubleshooting

- Run: `python demo_file_database.py` for full examples
- Run tests: `pytest tests/test_file_database.py -v`
- Use `overwrite=True` to replace existing projects
- Use SQLite browser tools to inspect `.db` files

---

## 🧬 Schema & Behavior Notes

- SQLite file includes:
  - `projects` table
  - `collar`, `survey`, `interval_*`, `point_*` tables
- Tables include original columns + `project_id` (if scoped)
- Per-hole queries use `WHERE HOLEID = ?` for efficient access

---

## ✅ Conclusion

The file backend is a drop-in alternative to the in-memory backend when:

- You need persistence
- You want memory efficiency
- You plan to share data via SQLite

Use:

- `DbConfig(backend='file', db_path=...)` to create file-backed databases
- `save_to_database()` to persist in-memory databases
- `link_to_database()` for large datasets with optimized access

For full examples, see:

- `demo_file_database.py`
- API reference in the project documentation
