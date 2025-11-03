# 7 - Preprocessing and Filtering Guide for `DrillholeDatabase`

This guide explains how to clean numerical columns and filter rows in a
`DrillholeDatabase` to prepare data for analysis. It focuses on two common,
chainable operations:

- `validate_numerical_columns`: convert and clean numerical columns
- `filter_by_nan_threshold`: remove rows with too many missing values

Both operations are designed to be simple, predictable, and chainable with other
filters (e.g., `.filter(holes=[...])`).

---

## 🎯 Goals

- Ensure numeric columns contain valid numeric values (e.g., strings → NaN)
- Remove or mark invalid values (e.g., negative or zero) based on context
- Filter rows based on completeness across key columns

---

## 1. ✅ Validating and Cleaning Numerical Columns

**Purpose**: Ensure selected columns contain numeric data and optionally treat
negative/zero values as missing.

**API**:

```python
validate_numerical_columns(table_name, columns, table_type="point", allow_negative=False)
```

**Behavior Summary**:

- Coerces values to numeric; non-convertible values become `NaN`
- If `allow_negative=False`, values ≤ 0 become `NaN`
- If `allow_negative=True`, only negative values become `NaN`
- Missing columns trigger warnings but do not halt execution
- Returns `self` for method chaining

**Example**:

```python
db = db.validate_numerical_columns("assay", columns=["CU_PPM", "AU_PPM", "AG_PPM"], allow_negative=False)
```

**Tips**:

- Run early in preprocessing to ensure numeric types for downstream operations
- Exclude categorical/text columns from `columns`
- Conservative design: warns on missing columns, avoids exceptions

---

## 2. 🧹 Filtering by NaN (Completeness) Threshold

**Purpose**: Remove rows lacking sufficient valid (non-NaN) values across key
columns.

**API**:

```python
filter_by_nan_threshold(table_name, columns, threshold, table_type="point")
```

**Behavior Summary**:

- Counts non-NaN values per row
- Computes completeness ratio: `valid_count / len(columns)`
- Keeps rows where ratio ≥ `threshold`
- Returns a **new** `DrillholeDatabase` (preserves immutability)

**Parameters**:

- `columns`: list of columns to evaluate
- `threshold`: float between `0.0` and `1.0`

**Example**:

```python
filtered_db = db.filter_by_nan_threshold("assay", columns=["CU_PPM", "AU_PPM", "AG_PPM", "PB_PPM"], threshold=0.75)
```

**Edge Cases**:

- `threshold == 1.0`: keeps only fully complete rows
- `threshold == 0.0`: keeps all rows
- Empty `columns` list raises an error

---

## 3. 🔗 Typical Workflows and Chaining

### 1. Basic Cleaning + Strict Completeness

```python
clean_db = db.validate_numerical_columns("assay", ["CU_PPM", "AU_PPM", "AG_PPM"], allow_negative=False).filter_by_nan_threshold(
    "assay", ["CU_PPM", "AU_PPM", "AG_PPM"], threshold=0.9
)
```

### 2. Spatial + Preprocessing + Permissive Completeness

```python
clean_db = (
    db.validate_numerical_columns("assay", ["CU_PPM", "AU_PPM"], allow_negative=True)
    .filter(holes=["DH001", "DH002", "DH003"])
    .filter_by_nan_threshold("assay", ["CU_PPM", "AU_PPM", "AG_PPM"], threshold=0.5)
)
```

### 3. Interval Table Preprocessing

```python
db = db.validate_numerical_columns("lithology", ["SIO2"], table_type="interval", allow_negative=False)
filtered_db = db.filter_by_nan_threshold("lithology", ["SIO2", "AL2O3"], threshold=0.8, table_type="interval")
```

---

## 4. 🧠 Practical Recommendations

- Run `validate_numerical_columns` immediately after loading or joining data
- Set `allow_negative` based on variable semantics (e.g., `False` for assays)
- Use high thresholds (0.9–1.0) for modeling; lower thresholds (0.5–0.75) for
  exploration
- Chain operations for reproducible preprocessing pipelines

---

## 5. 🧪 Testing and Debugging Tips

### Inspect Dtypes and Sample Values

```python
print(db.tables["assay"][["CU_PPM", "AU_PPM"]].dtypes)
print(db.tables["assay"][["CU_PPM", "AU_PPM"]].head())
```

### Preview Completeness Before Filtering

```python
tbl = db.tables["assay"][["CU_PPM", "AU_PPM", "AG_PPM", "PB_PPM"]]
completeness = tbl.notna().sum(axis=1) / tbl.shape[1]
print(completeness.describe())
```

---

## 6. 📁 Where to Look for Examples

- `examples/example_preprocessing.py` — demo script with synthetic assay data
- `tests/test_preprocessing.py` — unit tests for edge cases and expected
  behavior

---

## 7. 🛠️ Design Notes

- `validate_numerical_columns` returns `self` for fluent chaining
- `filter_by_nan_threshold` returns a new filtered instance to preserve
  immutability
- Both methods are resilient to missing columns and emit warnings instead of
  errors
