# 5 – Preprocessing and Filtering

This guide explains how to clean numeric columns and filter rows in a `DrillholeDatabase` to prepare data for analysis. It focuses:

- **`validate_numerical_columns`**: Convert and clean numeric columns  
- **`filter_by_nan_threshold`**: Remove rows with too many missing values  
- **`filter`**: Basic row filtering by hole IDs, depth ranges, bounding box or using a custom expression

All three methods are designed to be chainable for building reproducible preprocessing pipelines.

---


## 1. Validating and Cleaning Numeric Columns

Make sure selected columns contain numeric data and optionally treat negative/zero values as missing. 
This is intended for assay or xrf data where non-numeric entries can be included and negative/zero values 
indicate below detection limit.


```python
validate_numerical_columns(
    table_name, columns, table_type="interval", allow_negative=False
)
```

**Behavior**:

- Converts values to numeric; non-convertible values become `NaN`  
- If `allow_negative=False`, values ≤ 0 become `NaN`  
- If `allow_negative=True`, all valid numerical data is kept  
- Missing columns trigger warnings but do not stop execution  
- Returns `self` for method chaining  

**Example**:

```python
db = db.validate_numerical_columns(
    "assay", columns=["CU_PPM", "AU_PPM", "AG_PPM"], allow_negative=False
)
```

---

## 2. Filtering by NaN Threshold

Remove rows that lack enough valid (non-NaN) values across key columns.

```python
filter_by_nan_threshold(table_name, columns, threshold, table_type="point")
```

**Behavior**:

- Counts non-NaN values per row  
- Computes completeness ratio: `valid_count / len(columns)`  
- Keeps rows where ratio ≥ `threshold`  
- Returns a **new** `DrillholeDatabase` (preserves immutability)  

**Parameters**:

- `columns`: list of columns to check  
- `threshold`: float between `0.0` and `1.0`  

**Example**:

```python
filtered_db = db.filter_by_nan_threshold(
    "assay", columns=["CU_PPM", "AU_PPM", "AG_PPM", "PB_PPM"], threshold=0.75
)
```

**Edge Cases**:

- `threshold == 1.0`: keeps only fully complete rows  
- `threshold == 0.0`: keeps all rows  
- Empty `columns` list raises an error  

---

## 3. Typical Workflows

### Basic Cleaning + Strict Completeness

```python
clean_db = db.validate_numerical_columns(
    "assay", ["CU_PPM", "AU_PPM", "AG_PPM"], allow_negative=False
).filter_by_nan_threshold("assay", ["CU_PPM", "AU_PPM", "AG_PPM"], threshold=0.9)
```

### Hole ID + Preprocessing + Permissive Completeness

```python
clean_db = (
    db.validate_numerical_columns("assay", ["CU_PPM", "AU_PPM"], allow_negative=True)
    .filter(holes=["DH001", "DH002", "DH003"])
    .filter_by_nan_threshold("assay", ["CU_PPM", "AU_PPM", "AG_PPM"], threshold=0.5)
)
```

### Advanced: Preprocessing + Depth Range + Completeness

```python
clean_db = (
    db.validate_numerical_columns("assay", ["CU_PPM", "AU_PPM"], allow_negative=False)
    .filter(depth_range=(50, 200))
    .filter_by_nan_threshold("assay", ["CU_PPM", "AU_PPM", "AG_PPM"], threshold=0.8)
)
```
---
### Advanced: Map Bounding Box + Preprocessing + Completeness

```python
clean_db = (
    db.validate_numerical_columns("assay", ["CU_PPM", "AU_PPM"], allow_negative=False)
    .filter(bounding_box=(100, 200, 1000, 1100))
    .filter_by_nan_threshold("assay", ["CU_PPM", "AU_PPM", "AG_PPM"], threshold=0.7)
)
```


 

