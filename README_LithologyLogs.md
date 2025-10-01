# LithologyLogs - Lithological Data Preprocessing

The `LithologyLogs` class provides preprocessing tools for lithological drillhole data, enabling extraction of contacts, smoothing of intervals, and identification of lithological pairs.

## Overview

When using drillhole data for geological modelling, lithological logs need preprocessing to identify key geological features such as:
- Contacts between different rock types
- Basal contacts following stratigraphic sequences
- Statistical patterns in lithological transitions
- Smoothed representations of noisy data

The `LithologyLogs` class provides methods for these operations and can store processed results as new tables in the drillhole database.

## Installation

The class is part of the `loopresources.analysis` module:

```python
from loopresources.analysis import LithologyLogs
from loopresources.drillhole import DrillholeDatabase
```

## Quick Start

```python
import pandas as pd
from loopresources.drillhole import DrillholeDatabase, DhConfig
from loopresources.analysis import LithologyLogs

# Create or load a drillhole database
db = DrillholeDatabase(collar_data, survey_data)
db.add_interval_table('geology', geology_data)

# Initialize LithologyLogs
litho_logs = LithologyLogs(db, 'geology')

# Extract contacts between lithologies
contacts = litho_logs.extract_contacts(store_as='contacts')

# Extract basal contacts following stratigraphic order
lithology_order = ['sandstone', 'granite', 'schist']
basal_contacts = litho_logs.extract_basal_contacts(lithology_order, store_as='basal_contacts')

# Apply smoothing filter
smoothed = litho_logs.apply_smoothing_filter(window_size=3, store_as='geology_smoothed')

# Identify lithological pairs
pairs = litho_logs.identify_lithological_pairs()

# Calculate contact orientations
orientations = litho_logs.calculate_contact_orientations(store_as='contact_orientations')
```

## Methods

### Constructor

```python
LithologyLogs(database, interval_table_name, lithology_column='LITHO')
```

**Parameters:**
- `database`: DrillholeDatabase instance containing the lithology data
- `interval_table_name`: Name of the interval table with lithology data
- `lithology_column`: Name of the column containing lithology labels (default: 'LITHO')

### extract_contacts()

Extract all contacts between different lithologies within each drillhole.

```python
contacts = litho_logs.extract_contacts(store_as='contacts')
```

**Parameters:**
- `store_as`: Optional name to store result as a point table

**Returns:**
DataFrame with columns:
- `HOLEID`: Drillhole identifier
- `DEPTH`: Depth of the contact
- `LITHO_ABOVE`: Lithology above the contact
- `LITHO_BELOW`: Lithology below the contact

**Example:**
```
HOLEID  DEPTH  LITHO_ABOVE  LITHO_BELOW
DH001   30.0   granite      schist
DH001   80.0   schist       granite
```

### extract_basal_contacts()

Extract basal contacts (bottom boundaries) for lithologies following a specified stratigraphic order.

```python
basal_contacts = litho_logs.extract_basal_contacts(
    lithology_order=['sandstone', 'granite', 'schist'],
    store_as='basal_contacts'
)
```

**Parameters:**
- `lithology_order`: Ordered list of lithology names from top to bottom
- `store_as`: Optional name to store result as a point table

**Returns:**
DataFrame with columns:
- `HOLEID`: Drillhole identifier
- `DEPTH`: Depth of the basal contact
- `LITHO`: Lithology unit

**Use Case:**
When modelling stratigraphic sequences, basal contacts define the lower boundaries of geological units. This method extracts these boundaries while respecting the expected stratigraphic order.

### apply_smoothing_filter()

Apply a moving average smoothing filter to lithology intervals.

```python
smoothed = litho_logs.apply_smoothing_filter(
    window_size=3,
    store_as='geology_smoothed'
)
```

**Parameters:**
- `window_size`: Size of the smoothing window (number of intervals)
- `store_as`: Optional name to store result as an interval table

**Returns:**
DataFrame with smoothed interval boundaries

**Use Case:**
Geological logging can be noisy, with small intervals that may not be geologically significant. Smoothing can help identify major trends while reducing noise.

### identify_lithological_pairs()

Identify and count all unique pairs of adjacent lithologies across all drillholes.

```python
pairs = litho_logs.identify_lithological_pairs(store_as='litho_pairs')
```

**Parameters:**
- `store_as`: Optional name to store individual contacts as a point table

**Returns:**
DataFrame with columns:
- `LITHO_ABOVE`: Upper lithology in the pair
- `LITHO_BELOW`: Lower lithology in the pair
- `COUNT`: Number of times this pair occurs
- `HOLES`: Comma-separated list of hole IDs where pair occurs

**Example:**
```
LITHO_ABOVE  LITHO_BELOW  COUNT  HOLES
granite      schist       5      DH001,DH002,DH003
schist       granite      3      DH001,DH002
```

**Use Case:**
Understanding which lithological transitions are common helps validate geological models and identify important contacts for structural modelling.

### calculate_contact_orientations()

Calculate the orientation of lithological contacts using nearest neighbor analysis.

```python
orientations = litho_logs.calculate_contact_orientations(
    radius=500.0,
    min_neighbors=3,
    store_as='contact_orientations'
)
```

**Parameters:**
- `radius`: Search radius for nearest neighbors in 3D space (optional). If None, uses 2x the average spacing between drillhole collars.
- `min_neighbors`: Minimum number of neighbors required to fit a plane (default: 3)
- `store_as`: Optional name to store result as a point table

**Returns:**
DataFrame with columns:
- `HOLEID`: Drillhole identifier
- `DEPTH`: Depth of the contact
- `LITHO_ABOVE`, `LITHO_BELOW`: Lithologies on either side
- `x`, `y`, `z`: 3D coordinates of the contact (desurveyed)
- `nx`, `ny`, `nz`: Normal vector components (unit vector)
- `dip`: Dip angle from horizontal in degrees (0-90)
- `azimuth`: Strike azimuth in degrees (0-360, North = 0)
- `n_neighbors`: Number of neighbors used for plane fitting

**Algorithm:**
1. Extracts all lithology contacts
2. Desurveys contacts to 3D coordinates
3. Uses BallTree to find nearest neighbor contacts within radius
4. Fits a plane to neighbor points using Principal Component Analysis (PCA)
5. Extracts normal vector (perpendicular to contact surface)
6. Converts to geological dip and azimuth conventions

**Use Case:**
Contact orientations are essential for 3D geological modelling. By analyzing multiple contact points from different drillholes, this method estimates the spatial orientation of lithological boundaries. The normal vector points perpendicular to the contact surface and can be used as structural data for implicit modelling methods.

**Example:**
```
HOLEID  DEPTH  dip    azimuth  n_neighbors
DH001   30.0   45.2   125.3    5
DH002   40.0   43.8   128.7    7
```

In this example, both contacts dip at approximately 45° with a strike azimuth around 125-130°, suggesting a consistent geological structure.

## Storage of Results

All methods support an optional `store_as` parameter. When provided:
- Contact-based results are stored as **point tables** in the database
- Smoothed intervals are stored as **interval tables** in the database

Stored tables can be accessed later:

```python
# Access stored contacts
contacts = db.points['contacts']

# Access smoothed geology
smoothed = db.intervals['geology_smoothed']

# Export for use in LoopStructural
db.to_loopstructural_contacts('contacts')
```

## Example Workflow

See `demo_lithology_logs.py` for a complete example showing:
1. Creating a drillhole database with lithology data
2. Extracting all types of contacts
3. Applying smoothing filters
4. Identifying lithological patterns
5. Calculating contact orientations
6. Storing and accessing results

## Integration with Drillhole Database

The `LithologyLogs` class is designed to work seamlessly with the `DrillholeDatabase` class:

- **Non-destructive**: Original data is never modified
- **Flexible storage**: Results can be stored as new tables or used directly
- **Database integration**: Stored tables follow the same conventions as other drillhole data
- **Export ready**: Processed results can be exported to LoopStructural or other formats

## Notes

- All methods process each drillhole independently to maintain data integrity
- Intervals are automatically sorted by depth within each hole
- Contact extraction only identifies boundaries between different lithologies
- Smoothing preserves lithology labels while adjusting interval boundaries
- Pair identification handles both directions of transitions (A→B and B→A as separate pairs)

## Requirements

- pandas
- numpy
- scipy (for smoothing filters)
- scikit-learn (for BallTree nearest neighbor search)
- loopresources (drillhole module)
