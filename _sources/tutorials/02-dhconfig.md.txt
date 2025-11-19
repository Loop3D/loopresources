# 3 - DhConfig and required columns
### DhConfig required columns
The `DrillholeDatabase` requires certain columns to be present in the collar, survey and log files.
These are defined in the `DhConfig` class.
The required columns for collars and surveys are:
#### Collar required columns:
  - `holeid`: Unique identifier for each drillhole
  - `x`: Easting coordinate of the collar
  - `y`: Northing coordinate of the collar
  - `z`: Elevation of the collar
  - `total_depth`: Total depth of the drillhole
#### Survey required columns:
  - `holeid`: Unique identifier for each drillhole
  - `depth`: Depth along the drillhole
  - `azimuth`: Azimuth angle of the drillhole at the survey point
  - `dip`: Dip angle of the drillhole at the survey point
#### Interval log required columns:
   - `holeid`: Unique identifier for each drillhole
   - `from_depth`: From depth of the interval
   - `to_depth`: To depth of the interval
#### Point log required columns:
  - `holeid`: Unique identifier for each drillhole
  - `depth`: Depth along the drillhole
#### Orientation extras:
  - `alpha`: Alpha angle for orientation measurements
  - `beta`: Beta angle for orientation measurements
  - `gamma`: Gamma angle for orientation measurements
#### Extra config:
  - `positive_dips_down`: Boolean indicating whether positive dips should be interpreted as dipping down (default is False)
  - `debug`: Boolean to enable debug mode (default is False) debug mode provides additional logging information for troubleshooting and may exit on errors instead of attempting to continue processing.

### Customising DhConfig
There are two options, you can use the default column names defined in `DhConfig`, and load the CSV files directly, or you can provide a mapping from your CSV column names to the required `DhConfig` names.
Or you can modify the config to match your column names by setting the class variables directly, e.g. `DhConfig.holeid = "MY_HOLE_ID"`.

### Exporting/Importing DhConfig
You can also create a custom `DhConfig` by modifying the class variables directly. 
The config can the be exported as a dictionary `to_dict()` or json `to_json` and loaded using `from_config` or `from_file` methods. 
