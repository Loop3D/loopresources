import numpy as np
import pandas as pd


class DrillHole:
    collar: pd.DataFrame
    survey: pd.DataFrame

    @property
    def collar(self):
        return np.array([self.collar_x, self.collar_y, self.collar_z])

    @property
    def trace(self):
        pass
