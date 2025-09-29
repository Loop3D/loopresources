from typing import Optional
import pandas as pd
import numpy as np
import numpy.typing as npt
from scipy.interpolate import interp1d

from loopresources.drillhole.dhconfig import DhConfig
from .. import PRIVATE_DEPTH


class DataFrameInterpolator:
    def __init__(
        self,
        dataframe: pd.DataFrame,
        depth: str,
        columns: Optional[npt.ArrayLike] = None,
        fill_value: float = np.nan,
        bounds_error=False,
    ):
        """A class for interpolating properties in a dataframe
        along a continuous axis e.g. depth

        Parameters
        ----------
        dataframe : pd.DataFrame
            Pandas dataframe to interpolate the values from
        depth : str
            name of the depth column
        columns : npt.ArrayLike, optional
            List of columns to interpolate, by default interpolates all columns in the dataframe except depth
        fill_value : npt.ArrayLike, optional
            fill value for data interpolator when outside range, by default np.nan
        bounds_error : bool, optional
            Whether to throw exception when outside range, by default False
        """

        self.dataframe = dataframe.dropna(how="any")
        self.depth = depth
        self.columns_to_interpolate = (
            columns
            if columns is not None
            else [
                col
                for col in self.dataframe.columns
                if col != self.depth and col != DhConfig.holeid
            ]
        )
        self.interpolators = {}
        for c in self.columns_to_interpolate:
            try:
                self.interpolators[c] = interp1d(
                    self.dataframe[self.depth].to_numpy(),
                    self.dataframe[c].to_numpy(),
                    fill_value=fill_value,
                    bounds_error=bounds_error,
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
        if cols is None:
            cols = self.columns_to_interpolate
        deptharr = np.array(depth)
        result = pd.DataFrame(
            np.zeros((deptharr.shape[0], len(self.columns_to_interpolate) + 1)),
            columns=[PRIVATE_DEPTH] + self.columns_to_interpolate,
        )

        result[PRIVATE_DEPTH] = deptharr
        for c in self.columns_to_interpolate:
            result[c] = self.interpolators[c](depth)
        if issubclass(type(depth), (pd.Series, pd.DataFrame)):
            result = result.set_index(depth.index)
        return result.drop(columns=[PRIVATE_DEPTH])
