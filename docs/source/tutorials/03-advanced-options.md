# 3 — Advanced Options

This lesson covers advanced options and features available via `from_csv()`.

## Passing pandas `read_csv` options

You can forward any parameter accepted by `pandas.read_csv()` to the method.
Common uses:

```python
db = DrillholeDatabase.from_csv(
    collar_file="collar.csv",
    survey_file="survey.csv",
    sep=",",
    encoding="utf-8",
    skiprows=1,
)
```

## Angle normalization

- `from_csv()` detects angles in degrees and converts to radians where required.

## Column preservation

- Columns not used in mapping are preserved in the resulting dataframes so you
  retain metadata.
