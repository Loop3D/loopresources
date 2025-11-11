# 4 — Complete Example

A full example using Thalanga CSV files included in the `examples/thalanga`
folder.

```python
from loopresources.drillhole import DrillholeDatabase, DhConfig

# Load data with column mapping
db = DrillholeDatabase.from_csv(
    collar_file="examples/thalanga/ThalangaML_collar.csv",
    survey_file="examples/thalanga/ThalangaML_survey.csv",
    collar_columns={"holeid": "HOLE_ID", "x": "X_MGA", "y": "Y_MGA", "z": "Z_MGA", "total_depth": "DEPTH"},
    survey_columns={"holeid": "Drillhole ID", "depth": "Depth", "azimuth": "Azimuth", "dip": "Dip"},
)
db.add_interval_table(
    name="lithology",
    df="examples/thalanga/ThalangaML_lithology.csv",
    column_mapping={"holeid": "HOLE_ID", "sample_from": "FROM", "sample_to": "TO", "lithology": "LITHOLOGY"},
)
print(f"Loaded {len(db.list_holes())} drillholes")
print(f"Extent: {db.extent()}")

# Access an individual hole
hole = db[db.list_holes()[0]]
print(f"Total depth: {hole.collar[DhConfig.total_depth].iloc[0]}")


```
