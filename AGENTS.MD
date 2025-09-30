# agents.md

This document describes the intended role of coding assistants (e.g. GitHub
Copilot, ChatGPT) for the **drillhole-database** project. It combines the **data
model** (collar, survey, intervals, points) with the **LoopStructural export
options** to ensure a consistent, pandas-native workflow.

---

## Project Overview

The goal of this library is to provide a **Pythonic, pandas-native API** for
managing drillhole datasets, and to support robust export of constraints into
the **LoopStructural** implicit modelling ecosystem.

Drillhole datasets typically include:

- **Collar** — drillhole start location and metadata.
- **Survey** — downhole deviation data defining hole trajectory.
- **Intervals** — assays, geology, geotech, defined by depth `FROM`–`TO`.
- **Points** — measurements at a single depth (e.g. downhole geophysics).

---

## Data Model

The drillhole library is built around a **two-tiered data model**:

1. **`DrillholeDatabase`** – the main container for all drillhole data.
2. **`DrillHole`** – a per-hole view providing convenient access and operations
   for a single hole.

### DrillholeDatabase

The `DrillholeDatabase` stores global data as pandas DataFrames and
dictionaries:

```python
class DrillholeDatabase:
    collar: pd.DataFrame            # one row per drillhole
    survey: pd.DataFrame            # one row per survey station
    intervals: dict[str, pd.DataFrame]  # interval tables keyed by name
    points: dict[str, pd.DataFrame]     # point tables keyed by name

    def __getitem__(self, hole_id: str) -> "DrillHole":
        """Return a DrillHole view for a given HOLE_ID."""

    def filter(self, ...) -> "DrillholeDatabase":
        """Return a filtered database by holes, bounding box, depth, or expression."""

    def add_interval_table(self, name: str, df: pd.DataFrame):
        """Register a new interval table."""

    def add_point_table(self, name: str, df: pd.DataFrame):
        """Register a new point table."""

    def list_holes(self) -> list[str]:
        """Return all HOLE_IDs."""

    def extent(self) -> tuple[float,float,float,float,float,float]:
        """Return (xmin, xmax, ymin, ymax, zmin, zmax)."""
```

---

### DrillHole

Each `DrillHole` is a **view of the DrillholeDatabase** for a single `HOLE_ID`.
It provides per-hole access, sampling, and visualization:

```python
class DrillHole:
    collar: pd.DataFrame
    survey: pd.DataFrame
    database: DrillholeDatabase
    hole_id: str

    def __getitem__(self, propertyname: str) -> pd.DataFrame:
        """Return a single interval or point table for this hole."""

    def interval_tables(self) -> dict[str, pd.DataFrame]:
        """Return all interval tables for this hole."""

    def point_tables(self) -> dict[str, pd.DataFrame]:
        """Return all point tables for this hole."""

    def trace(self, step: float = 1.0) -> pd.DataFrame:
        """Return the interpolated XYZ trace of the hole."""

    def depth_at(self, x: float, y: float, z: float) -> float:
        """Return depth along hole closest to a given XYZ point."""

    def sample(self, propertyname: str, step: float = 1.0) -> pd.DataFrame:
        """Resample interval/point data onto the interpolated trace."""

    def vtk(self, interval: str = None) -> "pv.PolyData":
        """
        Return a PyVista PolyData object of the drillhole.
        If `interval` is provided, color segments by that interval table.
        """
```

---

### Design Notes

- `DrillholeDatabase` acts as the **global manager**, responsible for
  validation, filtering, and LoopStructural export.
- `DrillHole` acts as a **per-hole interface**, giving convenient access to
  intervals, points, traces, and visualization.
- `__getitem__` on the database returns a `DrillHole` view (`db["DH001"]`).
- `__getitem__` on a `DrillHole` returns a **property table**
  (`hole["geology"]`).
- Methods like `trace`, `sample`, and `vtk` bridge **tabular data** to **spatial
  geometry**.
- Filtering operations on `DrillholeDatabase` return **new instances** to
  preserve immutability.

---

This structure ensures a **clear separation of global vs per-hole operations**,
while maintaining **pandas-native storage** and **LoopStructural export
compatibility**.

### Collar

- Required: `HOLE_ID`, `X`, `Y`, `Z`, `TOTAL_DEPTH`.
- Optional: `AZIMUTH`, `DIP`.

### Survey

- Required: `HOLE_ID`, `DEPTH`, `AZIMUTH`, `DIP`.
- Ordered by depth.

### Intervals

- Required: `HOLE_ID`, `FROM`, `TO`.
- Measurement columns: `LITHO`, `CU_PPM`, etc.

### Points

- Required: `HOLE_ID`, `DEPTH`.
- Measurement columns: `density`, `gamma`, etc.

Validation ensures:

- All `HOLE_ID`s exist in collar.
- Depths don’t exceed `TOTAL_DEPTH`.
- Intervals don’t overlap.

---

## Core Methods

-
- `validate()` — schema and consistency checks.
- `interpolate_trace(hole_id, step=1.0)` — return XYZ along hole at regular
  depth steps.
- `map_intervals_to_xyz(table_name)` — convert interval boundaries into XYZ
  coordinates.
- `map_points_to_xyz(table_name)` — convert depth points into XYZ coordinates.

---

## Filtering API

Filtering should be a **first-class operation** that returns a new
`DrillholeDatabase` with only the relevant subset of data. This allows users to
export only the data needed for a specific modelling task.

### Method

```python
def filter(self,
           holes: list[str] = None,
           bbox: tuple[float,float,float,float] = None,
           depth_range: tuple[float,float] = None,
           expr: str | callable = None) -> "DrillholeDatabase":
    """
    Return a filtered DrillholeDatabase.

    Args:
        holes: list of HOLE_IDs to keep.
        bbox: (xmin, xmax, ymin, ymax) filter by collar XY.
        depth_range: (min_depth, max_depth) clip survey/interval/point data.
        expr: pandas query string or callable applied to intervals/points.
    """
```

### Filtering Strategy

- **Collar**: filter rows by `holes` or `bbox`.
- **Survey**: keep only rows where `HOLE_ID` matches filtered collars; clip by
  `depth_range`.
- **Intervals**: filter to matching `HOLE_ID`s, apply `expr`, clip by
  `depth_range`.
- **Points**: same as intervals.

### Examples

```python
# Keep only holes in bounding box
subset = db.filter(bbox=(500000, 501000, 6500000, 6501000))

# Keep only specific lithologies
sandstone = db.filter(expr="LITHO == 'sandstone'")

# Combine with depth clipping
shallow = db.filter(depth_range=(0, 200))

# Export filtered subset
contacts = shallow.to_loopstructural_contacts("geology", mode="contact")
```

---

## LoopStructural Export

LoopStructural requires structural constraints in specific formats. Export
functions are methods on `DrillholeDatabase`:

### Orientations

Exported from survey or structural intervals. Options:

1. **Normal vectors**

   - Columns: `X`, `Y`, `Z`, `nx`, `ny`, `nz`, `val`.

2. **Gradients**

   - Columns: `X`, `Y`, `Z`, `gx`, `gy`, `gz`, `val`.

3. **Strike & dip**

   - Columns: `X`, `Y`, `Z`, `strike`, `dip`, `polarity`.

Usage:

```python
orients = db.to_loopstructural_orientations("geology", mode="normal")
```

---

### Lithology / Stratigraphy

Derived from interval tables. Options:

1. **Contacts (`val=0`)**

   - Columns: `X`, `Y`, `Z`, `val=0`, `feature_name`.

2. **Inequality constraints (bounds)**

   - Columns: `X`, `Y`, `Z`, `val` (lower/upper).

3. **Inequality pairs (topology)**

   - Columns: `X`, `Y`, `Z`, `unit_A`, `unit_B`.

4. **Cumulative thickness (conformable stratigraphy)**

   - Columns: `X`, `Y`, `Z`, `val` (cumulative thickness).

Usage:

```python
contacts = db.to_loopstructural_contacts("geology", mode="contact")
pairs = db.to_loopstructural_contacts("geology", mode="pair")
```

---

## Assistant Guidelines

When generating code:

- Always represent drillhole data as pandas DataFrames.
- Ensure `X`, `Y`, `Z` columns are capitalized in LoopStructural exports.
- Normalize orientation vectors before exporting.
- Implement multiple export modes explicitly (`mode="..."`).
- Validate stratigraphy order before inequality exports.
- Use minimum curvature for survey interpolation.
- Filtering should always return a **new** `DrillholeDatabase`
  (non-destructive).

---

## Example Workflow

```python
# Build a database
db = DrillholeDatabase(collar_df, survey_df)
db.add_interval_table("geology", geology_df)

# Validate structure
db.validate()

# Filter subset
subset = db.filter(expr="LITHO == 'sandstone'", depth_range=(0, 200))

# Export orientations
orients = subset.to_loopstructural_orientations("geology", mode="strike_dip")

# Export stratigraphic contacts as inequality pairs
pairs = subset.to_loopstructural_contacts("geology", mode="pair")

# Pass to LoopStructural
from LoopStructural import GeologicalModel
model = GeologicalModel(bounding_box)
feature = model.create_and_add_foliation('litho',data=pd.concat([orients,pairs],ignore_index=True))
```

---

## Future Extensions

- GeoParquet export for efficient I/O.
- Integration with `pyvista` for pre-modelling visualization.
- Support for uncertainty fields in exports.
- Automatic stratigraphic column ordering for inequality pairs.

---
