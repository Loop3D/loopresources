# 2 - Basic Usage

This tutorial shows how to load collar and survey CSV files into a
`DrillholeDatabase`.


### Loading from CSV files

### When columns match DhConfig names

```python
from loopresources.drillhole import DrillholeDatabase

db = DrillholeDatabase.from_csv(collar_file="collar.csv", survey_file="survey.csv")
```

### When you need to map columns

```python
from loopresources.drillhole import DrillholeDatabase, DhConfig

db = DrillholeDatabase.from_csv(
    collar_file="path/to/collar.csv",
    survey_file="path/to/survey.csv",
    collar_columns={
        DhConfig.holeid: "HOLE_ID",
        DhConfig.x: "X_MGA",
        DhConfig.y: "Y_MGA",
        DhConfig.z: "Z_MGA",
        DhConfig.total_depth: "DEPTH",
    },
    survey_columns={
        DhConfig.holeid: "Drillhole ID",
        DhConfig.depth: "Depth",
        DhConfig.azimuth: "Azimuth",
        DhConfig.dip: "Dip",
    },
)
```

Notes:

- Extra columns are preserved.
- Required columns must be present after mapping.

### List drillholes in the database

```python
db.list_holes()
```

### Access individual drillholes

You can access individual drillholes using their hole ID as the key.
```python
dh = db["Hole_001"]
print(dh)
```

### Iterating over drillholes
You can iterate over all drillholes in the database.
```python
for dh in db:
    print(dh.holeid)
```

### Get coordinate extent of the database
The extent of the database is a LoopStructural bounding box
```python
extent = db.extent()
print(extent)
```

### Attaching lithology and assay data
You can attach lithology and assay data to the drillholes after loading the database.
```python
db.add_interval_table("lithology", '/path/to/lithology.csv',column_mapping={
    DhConfig.holeid: "Drillhole ID",
    DhConfig.from_depth: "From",
    DhConfig.to_depth: "To",
})
```
This will add the lithology intervals to each drillhole based on the provided CSV file.

### Desurveying drillholes to 3D points
You can convert drillhole surveys with associated logs to 3D points using the `desurvey_intervals` method, where the table name is the name you provided when adding the interval table.
```python
desurveyed = dh.desurvey_intervals(table_name)
```
This will return a table of with the interval logs and associated 3D coordinates as well as the dip and azimuth of the drill hole at those points.

### Attaching point data

You can also attach point data to the drillholes.
```python
db.add_point_table("structures", '/path/to/structures.csv', column_mapping={
    DhConfig.holeid: "Drillhole ID",
    DhConfig.depth: "FROM,
})
```
This will add the point data to each drillhole based on the provided CSV file.

You can desurvey these points to get their 3D coordinates:
```python
desurveyed_points = dh.desurvey_points("structures")
```
This will return a table of the point data with associated 3D coordinates and the orientation of the drill hole.

### Converting from alpha beta and gamma to strike and dip

```Python
orientations = db.alpha_beta_to_orientation('structures')
```

This will return a table of the point data with associated strike and dip based on the alpha, beta and gamma angles provided in the point table.
