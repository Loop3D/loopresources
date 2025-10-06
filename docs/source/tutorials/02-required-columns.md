# 2 — Required Columns & Validation

This lesson explains the columns `from_csv()` requires and the validation
performed.

## Collar CSV required fields

- `holeid` — Unique identifier
- `x` — Easting
- `y` — Northing
- `z` — Elevation
- `total_depth` — Total hole depth

## Survey CSV required fields

- `holeid` — Must match collar `holeid`
- `depth` — Depth along hole
- `azimuth` — Azimuth angle
- `dip` — Dip angle

Validation performed by `from_csv()`:

- Ensures required columns exist after mapping
- Removes rows with missing essential data
- Checks for duplicate hole IDs
- Verifies survey holes exist in collar data

Error examples raised by the method:

- Missing mapped column:
  `ValueError: Column 'INVALID_COLUMN' specified in collar_columns mapping not found`
- Missing required columns after mapping:
  `ValueError: Missing required collar columns: ['HOLEID', 'EAST']`
- Duplicate hole IDs: `ValueError: Duplicate HOLE_IDs found in collar data`
- Survey holes not in collar:
  `ValueError: Survey holes not found in collar: {'DH999'}`
