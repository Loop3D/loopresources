# 6 – String Representations: Advanced Debugging & Inspection Guide

This guide explains how to use the `__repr__` and `__str__` methods implemented
in `DrillHole`, `DrillholeDatabase`, and `DhConfig` for advanced inspection,
debugging, and automated testing. It covers how to interpret outputs, diagnose
common data issues, customize displays, and integrate these representations into
your workflows.

---

## 📌 Audience

- **Developers** building on `loopresources` who need fast diagnostics
- **Test authors** validating object state in unit tests
- **Analysts** investigating data quality and structural issues interactively

---

## 🧠 Why These Representations Matter

- `__repr__`: concise, machine-friendly summaries ideal for logs and assertions
- `__str__`: expanded, human-readable views with statistics and diagnostics
- Automatically informative in REPLs and notebooks — no method calls required

---

## 📦 What’s Covered

- **Classes**: `DrillHole`, `DrillholeDatabase`, `DhConfig`
- **Outputs**: hole identity, depth, spatial extent, table dimensions, stats,
  NaNs

---

## ⚡ Quick Reference: Behavior

### `DrillHole`

- `__repr__`:

  ```python
  DrillHole(hole_id="DH001", depth=150.00)
  ```

  _Single-line summary — safe for logs_

- `__str__`: _Multi-line diagnostics — includes location, depth, azimuth/dip
  averages, table summaries_

### `DrillholeDatabase`

- `__repr__`:

  ```python
  DrillholeDatabase(holes=5, interval_tables=2, point_tables=1)
  ```

  _Single-line dataset summary_

- `__str__`: _Dataset-level diagnostics — hole count, spatial extent, table
  stats, data coverage_

### `DhConfig`

- `__str__`: _Compact mapping of column configurations and flags_

---

## 🧪 Examples for Debugging

### 1. Spot Missing Spatial Data

```python
print(db)
# If spatial extent is tiny or empty, inspect collar rows for missing X/Y/Z
```

### 2. Verify a Hole’s Geometry

```python
hole = db["DH001"]
print(repr(hole))  # Quick log-friendly summary
print(hole)  # Detailed view: azimuth/dip averages, survey stats
```

### 3. Detect Sparse Tables

Use `DrillholeDatabase.__str__` to see how many holes contain data for each
table.

---

## 📊 Interpreting Statistics

- **Numerical columns**: mean, min, max, non-null count
- **Categorical columns**: unique counts and sample values
- **NaN counts**: inferred from non-null counts

---

## 🔍 Common Investigation Patterns

- **Zero rows**: check `DhConfig` mappings and `HOLEID` consistency
- **Tiny numeric ranges**: verify units and data types
- **Angle anomalies**: angles shown in degrees — check source units

---

## ✅ Using Representations in Tests

- Use `repr()` for concise, stable assertions

  ```python
  assert "DH001" in repr(hole)
  ```

- Prefer querying DataFrames over parsing `str()` output
- Include `str()` output in test logs for faster diagnosis

---

## 🛠️ Customization & Extension

- Safe to override — keep `repr()` concise, `str()` human-readable
- For advanced diagnostics, use methods like `hole.describe(verbose=True)`

---

## 🚀 Performance Considerations

- `__str__` computes aggregates — avoid in tight loops
- File backend (`DbConfig(backend='file')`) optimizes per-hole access
- Global `DrillholeDatabase.__str__` may still require full-table summaries

---

## 🧭 Debugging Best Practices

1. Start with `repr()` for quick object state
2. Use `print(obj)` for deeper diagnostics
3. For many holes, iterate and log `repr(hole)`
4. Use file backend for efficient inspection

---

## 🧰 Troubleshooting Checklist

- **Unexpected hole count**: check `HOLEID` casing and whitespace
- **Missing columns**: verify `DhConfig` mappings and CSV headers
- **Floating point instability**: round values or assert on raw numbers

---

## 🔗 Logging & CI Integration

- Use `repr()` in logs and CI messages — compact and deterministic
- Avoid asserting full `str()` layouts — prefer targeted checks or JSON
  diagnostics

---

## 📁 Codebase References

- `loopresources/drillhole/drillhole_database.py` — `DrillHole`,
  `DrillholeDatabase`
- `loopresources/drillhole/dhconfig.py` — `DhConfig.__str__`
- `tests/test_str_repr.py` — test cases and edge scenarios

---

## 📎 Appendix: Interpretation Cues

- **Zero-range spatial extent**: check for constant/missing coordinates
- **Partial table coverage**: compare `db.list_holes()` with table `HOLEID`s
- **Unrealistic azimuths (e.g., 370°)**: check if source data is in radians

---

## 🧾 Summary

Use `repr()` as a fast, machine-friendly probe and `str()` for detailed human
diagnostics. These representations help triage data quality and configuration
issues efficiently, while keeping APIs available for precise programmatic
checks.

For full examples, see:

- `tests/test_str_repr.py`
- `examples/` and `demo_*.py` scripts
