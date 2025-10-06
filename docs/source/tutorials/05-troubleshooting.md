# 5 — Troubleshooting

Common errors and how to fix them.

- Missing column in mapping: ensure the CSV contains the column name you
  referenced in the mapping.
- Required columns missing after mapping: double-check keys in `collar_columns`
  / `survey_columns` match method expectations.
- Duplicate hole IDs: inspect the collar CSV and remove or correct duplicates.
- Survey holes not found in collar: ensure holeids match exactly (watch for
  whitespace and casing).

Debug tips:

- Print the first rows of your CSV with `pd.read_csv(...).head()` to confirm
  column names.
- Use `.str.strip()` to remove accidental spaces in string columns.
