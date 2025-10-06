# String Representation — Advanced User & Debugging Guide

This guide explains how to use the rich `__repr__` and `__str__` implementations
added to `DrillHole`, `DrillholeDatabase`, and `DhConfig` as tools for advanced
inspection, debugging, and automated tests. It focuses on interpreting output,
diagnosing common data problems, customizing displays, and integrating these
representations into debugging workflows.

Audience

- Developers building on `loopresources` who need fast diagnostics
- Test authors validating object state in unit tests
- Analysts investigating data quality and structural issues interactively

Why these string representations matter for debugging

- `__repr__` provides concise, machine-friendly one-line summaries ideal for
  logs and assertion messages
- `__str__` provides an expanded human-readable view with statistics and counts
  that surface data quality issues at a glance
- They are intentionally informative without requiring explicit method calls,
  making REPL and notebook sessions more productive

What is covered

- Classes: `DrillHole`, `DrillholeDatabase`, `DhConfig`
- Key outputs: hole identity and depth, spatial extent, table row/column counts,
  numerical statistics, categorical uniques, NaN counts

Quick reference: behavior

- DrillHole.**repr**: single-line, e.g.
  `DrillHole(hole_id='DH001', depth=150.00m)` — safe to include in logs
- DrillHole.**str**: detailed multi-line per-hole diagnostics (location, depth,
  avg azimuth/dip, interval/point table summaries)
- DrillholeDatabase.**repr**: single-line summary, e.g.
  `DrillholeDatabase(holes=5, interval_tables=2, point_tables=1)`
- DrillholeDatabase.**str**: dataset-level diagnostics (number of holes, X/Y/Z
  extent, table row/col counts, holes-with-data counts)
- DhConfig.**str**: compact mapping table for column configuration and boolean
  flags

Examples for debugging

1. Quickly spot missing spatial data

```python
# In REPL or a test failure traceback
print(db)
# If spatial extent shows a tiny or empty range, inspect collar rows for missing X/Y/Z
```

2. Verify a single hole's interpolated geometry

```python
hole = db["DH001"]
print(repr(hole))  # quick check in logs
print(hole)  # expanded view: check average azimuth/dip and survey counts
```

3. Find tables missing values or incomplete coverage

- `DrillholeDatabase.__str__` lists how many holes have data for each
  interval/point table. Use this to detect tables that are sparsely populated.

Interpreting statistics

- Numerical columns: mean, min, max, non-null count. Large gaps between min/max
  vs expected ranges often indicate unit or scaling issues.
- Categorical columns: unique-value counts and example values. Unexpected
  singletons or many uniques may indicate parsing problems.
- NaN counts are surfaced via non-null counts; a low non-null count signals
  missing data.

Common investigations and patterns

- Unexpected zero rows for a table: verify column names in `DhConfig` and
  confirm `HOLEID` matches
- Many tiny numeric ranges: check units and dtype (ints vs floats) or accidental
  string parsing
- Angle anomalies: `__str__` converts angles to degrees for readability — check
  source data units if values look unrealistic

Using representations in tests

- Prefer asserting on `repr()` where you need stable, concise output (e.g.
  `assert 'DH001' in repr(hole)`)
- For content tests, parse `str()` output or, better, query the underlying
  DataFrames directly for deterministic assertions
- When tests fail showing large `str()` output, include the printed
  representation in test failure logs for faster diagnosis

Customizing and extending

- These methods are additive and safe to override; if customizing, keep `repr`
  concise and `str` human-focused
- To add bespoke debug info (e.g. provenance tags or compute-heavy diagnostics),
  consider adding a parameterized method (e.g. `hole.describe(verbose=True)`)
  rather than making `__str__` expensive

Performance considerations

- `__str__` computes aggregates; avoid calling it in performance-sensitive tight
  loops
- When using the file backend (`DbConfig(backend='file')`), per-hole
  `__str__`/`repr` access is optimized — only rows for that hole are fetched —
  but global `DrillholeDatabase.__str__` may still require summary queries
  against tables

Best practices for debugging sessions

1. Start with `repr()` to get a quick cursor into the object state
2. Use `print(obj)` for deeper diagnostics when needed
3. If investigating many holes, iterate using `for hole in db` and log
   `repr(hole)` rather than full `str()`
4. When performance is a concern, link to a file backend and inspect single
   holes rather than printing the entire database

Troubleshooting checklist

- Mismatch in expected hole count: confirm `HOLEID` casing and whitespace, then
  run `db.list_holes()`
- Missing columns in tables: verify `DhConfig` column mappings and input CSV
  headers
- Tests unstable due to floating point formatting: normalize by rounding values
  before string comparisons or assert on underlying numeric values

Integrating with logging and CI

- Use `repr()` output in debug logs and CI failure messages — it's compact and
  deterministic
- For CI snapshots, avoid asserting the entire `str()` layout; prefer targeted
  assertions or JSON-serializable diagnostics

Where to look in the codebase

- `loopresources/drillhole/drillhole_database.py` — implementations for
  `DrillHole` and `DrillholeDatabase` string methods
- `loopresources/drillhole/dhconfig.py` — `DhConfig.__str__`
- `tests/test_str_repr.py` — tests demonstrating expected outputs and edge cases

Appendix: quick examples and interpretation cues

- Spatial extent shows zero-range for X/Y/Z: check for constant coordinates or
  missing values
- Interval table shows `Holes with data: 3/5`: investigate which `HOLEID`s are
  absent by comparing `db.list_holes()` to unique values in the table
- `Average Azimuth: 370°` (or values outside 0–360): check whether data stored
  in radians or degrees; source data unit mismatch is likely

Summary

Treat `repr()` as the first-line, machine-friendly probe and `str()` as the
expanded human diagnostic. These string representations are designed to speed up
triage of data quality and configuration issues while keeping the underlying
APIs available for precise programmatic checks.

For full examples and usage patterns, see `tests/test_str_repr.py` and
interactive demos in the `examples/` and `demo_*.py` scripts.
