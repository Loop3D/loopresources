import dataclasses
from typing import Optional, List, Union
import numpy as np
import pandas as pd
from . import DhConfig


class DrillHole:
    collar: pd.DataFrame
    survey: pd.DataFrame

    @property
    def collar(self):
        return np.array([self.collar_x, self.collar_y, self.collar_z])

    @property
    def trace(self):
        desurvey(collar, survey)
