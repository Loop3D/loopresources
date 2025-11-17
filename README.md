# Loop.Resources

A module for resource estimation and associated utility functions

## Installation
```bash
pip install loopresources
```
## Features
- Drillhole database management
- Desurveying and 3D visualization
- Interval resampling and analysis
- File-based database backend with project support

## Usage
```python
from loopresources import DrillholeDatabase
import pyvista as pv

db = DrillholeDatabase.from_csv("path_to_collar.csv", "path_to_survey.csv")
db.add_interval_table("lithology", lithology_data)
desurveyed_lithology = db.desurvey_intervals("lithology")
p = pv.Plotter()
for h in db:
    p.add_mesh(h.vtk(radius=2.0))
p.show()
```

## Command Line Interface
LoopResources also provides a CLI for common tasks. Use `loopresources --help` to see available commands.

## Contributing
Contributions are welcome! Please submit issues and pull requests on the GitHub repository. 
## License
This project is licensed under the MIT License. See the LICENSE file for details.
