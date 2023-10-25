from geoh5py.workspace import Workspace
from geoh5py.groups import ContainerGroup
from geoh5py.objects import Points
import pandas as pd
from pandas.api.types import is_numeric_dtype
# Create a workspace
def add_points_to_geoh5(filename : str,points: pd.DataFrame,fields=[],group=None,name='desurveyed'):
    """
    Add points to a geoh5 file
    """
    with Workspace(filename) as ws:
        if not ws.get_entity(group)[0]:
            if group:
                group = ContainerGroup.create(ws, name=group)
            # group = ContainerGroup.create(ws, name='loop')
            points_obj = Points.create(ws, name=name, parent=group,vertices=points[['x','y','z']].values)
            data = {}
            # print(fields)
            for f in fields:
                try:
                    values = points[f].values
                    if not is_numeric_dtype(points[f]):
                        continue
                        
                    data[f] = {
                        "association":"VERTEX",
                        "values": values
                    }
                except Exception as e:
                    print(e)
            print(data)
            data_list = points_obj.add_data(data)
