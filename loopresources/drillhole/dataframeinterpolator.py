import pandas as pd
import numpy as np
import numpy.typing as npt
from scipy.interpolate import interp1d
from .. import PRIVATE_DEPTH


class DataFrameInterpolator:
    def __init__(self, dataframe: pd.DataFrame, depth: str):
        """A class for interpolating properties in a dataframe
        along a continuous axis e.g. depth

        Parameters
        ----------
        dataframe : pd.DataFrame
            _description_
        depth : str
            _description_
        """

        self.dataframe = dataframe
        self.depth = depth
        self.columns_to_interpolate = [
            col for col in self.dataframe.columns if col != self.depth
        ]
        self.interpolators = {}
        for c in self.columns_to_interpolate:
            try:
                self.interpolators[c] = interp1d(
                    self.dataframe[self.depth].to_numpy(),
                    self.dataframe[c].to_numpy(),
                    # fill_value=np.nan,
                    # bounds_error=False,
                )
            except:
                print(self.dataframe, c)

    def __call__(self, depth: npt.ArrayLike, cols=None) -> pd.DataFrame:
        """_summary_

        Parameters
        ----------
        depth : s
            npt.ArrayLike
        cols : _type_, optional
            List of columns that are to be interpolated, if none interpolate all columns, by default None

        Returns
        -------
        pd.DataFrame
            _description_
        """
        if cols == None:
            cols = self.columns_to_interpolate
        depth = np.array(depth)
        result = pd.DataFrame(
            np.zeros((depth.shape[0], len(self.columns_to_interpolate) + 1)),
            columns=[PRIVATE_DEPTH] + self.columns_to_interpolate,
        )

        result[PRIVATE_DEPTH] = depth
        for c in self.columns_to_interpolate:
            result[c] = self.interpolators[c](depth)
        return result
