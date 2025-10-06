# Preprocessing and Filtering Guide for DrillholeDatabase

This guide explains how to clean numerical columns and filter rows in a
DrillholeDatabase to prepare data for analysis. It focuses on two common,
chainable operations implemented on the DrillholeDatabase API:

- validate_numerical_columns: convert and clean numerical columns
- filter_by_nan_threshold: remove rows with too many missing values

Both operations are designed to be simple, predictable and chainable with other
filters (for example, spatial filters such as `.filter(holes=[...])`).

## Goals

- Ensure columns that should be numeric contain numeric values (strings → NaN,
  coercion where possible).
- Remove or mark invalid or non-meaningful values (negative or non-positive
  values) according to user needs.
- Filter rows that do not meet a minimum completeness threshold across a set of
  key columns.

## 1. Validating and cleaning numerical columns

Purpose: Make sure selected columns contain numeric data and optionally treat
negative/zero values as missing.

API:

- validate_numerical_columns(table_name, columns, table_type='point',
  allow_negative=False)

Behavior summary:

- Attempts to coerce values in each specified column to numeric (non-convertible
  values become NaN).
- If allow_negative is False, values <= 0 are replaced with NaN (useful for
  mass/ppm values where zero or negative is invalid).
- If allow_negative is True, only strictly negative values are replaced with
  NaN.
- Missing columns produce a warning; the method continues with existing columns.
- Returns self so calls can be chained.

Example:

```python
# Convert assay columns containing strings to numeric and replace <= 0 with NaN
db = db.validate_numerical_columns("assay", columns=["CU_PPM", "AU_PPM", "AG_PPM"], allow_negative=False)  # treat zero and negatives as missing
```

Notes and tips:

- Use this early in preprocessing so later filters and aggregations operate on
  numeric dtypes.
- If some columns are categorical or intentionally contain text, do not include
  them in `columns`.
- The method is conservative: it warns about missing columns rather than
  raising, keeping workflows resilient.

## 2. Filtering by NaN (completeness) threshold

Purpose: Remove rows that do not have a sufficient proportion of valid (non-NaN)
values across a set of important columns.

API:

- filter_by_nan_threshold(table_name, columns, threshold, table_type='point')

Behavior summary:

- Counts non-NaN entries per row among the given columns.
- Computes the proportion of valid values for each row (valid_count /
  len(columns)).
- Keeps only rows whose proportion >= threshold.
- Returns a new DrillholeDatabase instance containing the filtered rows
  (preserves immutability for filtering operations).

Parameters:

- columns: list of columns to evaluate completeness over.
- threshold: float between 0.0 and 1.0. For example, 0.75 requires at least 75%
  of the columns to be valid.

Example:

```python
# Keep rows where at least 3 of 4 assay columns are present
filtered_db = db.filter_by_nan_threshold("assay", columns=["CU_PPM", "AU_PPM", "AG_PPM", "PB_PPM"], threshold=0.75)
```

Edge cases:

- threshold == 1.0 keeps only rows with all columns present and non-NaN.
- threshold == 0.0 keeps all rows (no filtering).
- If the columns list is empty, the method raises an error — the operation
  requires at least one column.

## 3. Typical workflows and chaining

Both methods are designed to work together and with the existing `filter()` API.
Example preprocessing workflows:

1. Basic cleaning and strict completeness:

```python
clean_db = db.validate_numerical_columns("assay", ["CU_PPM", "AU_PPM", "AG_PPM"], allow_negative=False).filter_by_nan_threshold(
    "assay", ["CU_PPM", "AU_PPM", "AG_PPM"], threshold=0.9
)
```

2. Spatial + preprocessing + permissive completeness:

```python
clean_db = (
    db.validate_numerical_columns("assay", ["CU_PPM", "AU_PPM"], allow_negative=True)
    .filter(holes=["DH001", "DH002", "DH003"])
    .filter_by_nan_threshold("assay", ["CU_PPM", "AU_PPM", "AG_PPM"], threshold=0.5)
)
```

3. Preprocessing intervals (interval tables):

```python
# Specify table_type='interval' for interval tables
db = db.validate_numerical_columns("lithology", ["SIO2"], table_type="interval", allow_negative=False)
filtered_db = db.filter_by_nan_threshold("lithology", ["SIO2", "AL2O3"], threshold=0.8, table_type="interval")
```

## 4. Practical recommendations

- Validate numeric columns as soon as you read or join data into the
  DrillholeDatabase.
- Choose allow_negative based on the physical meaning of the variable (e.g.,
  assays: allow_negative=False; deviations or residuals: allow_negative=True).
- Use a stringent threshold (0.9–1.0) for models that require nearly-complete
  feature sets; use lower thresholds (0.5–0.75) for exploratory tasks.
- Chain operations to keep preprocessing compact and reproducible.

## 5. Testing and debugging hints

- After validate_numerical_columns, inspect dtypes and a value sample:

```python
print(db.tables["assay"][["CU_PPM", "AU_PPM"]].dtypes)
print(db.tables["assay"][["CU_PPM", "AU_PPM"]].head())
```

- To understand how many rows will be removed by a threshold before applying it,
  compute the completeness proportions:

```python
tbl = db.tables["assay"][["CU_PPM", "AU_PPM", "AG_PPM", "PB_PPM"]]
completeness = tbl.notna().sum(axis=1) / tbl.shape[1]
print(completeness.describe())
```

## 6. Where to look for examples

- See `examples/example_preprocessing.py` for a short script that demonstrates
  these operations on synthetic assay data.
- Tests in `tests/test_preprocessing.py` demonstrate corner cases and expected
  behavior.

## 7. Design notes (short)

- validate_numerical_columns returns self to fit fluent preprocessing chains on
  the same database object.
- filter_by_nan_threshold returns a new filtered database to match the existing
  filter semantics and preserve safe immutability when filtering.
- Both methods are resilient to missing columns and provide clear warnings
  rather than failing by default.

For questions about a specific dataset or to request additional preprocessing
utilities (e.g., imputation, outlier clipping, or scaling helpers), include a
short example of the input table and the desired output and an example workflow
will be provided.
