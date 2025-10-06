"""Utilities for interpolating columns in drillhole dataframes."""

from typing import Optional
import pandas as pd
import numpy as np
import numpy.typing as npt
from scipy.interpolate import interp1d

from loopresources.drillhole.dhconfig import DhConfig
from .. import PRIVATE_DEPTH


class DataFrameInterpolator:
    """Interpolate properties along a continuous axis (e.g. depth)."""

    def __init__(
        self,
        dataframe: pd.DataFrame,
        depth: str,
        columns: Optional[npt.ArrayLike] = None,
        fill_value: float = np.nan,
        bounds_error=False,
    ):
        """Create an interpolator for a dataframe.

        Parameters
        ----------
        dataframe : pd.DataFrame
            Pandas dataframe to interpolate the values from.
        depth : str
            Name of the depth column.
        columns : npt.ArrayLike, optional
            List of columns to interpolate; by default interpolates all columns
            in the dataframe except the depth column.
        fill_value : npt.ArrayLike, optional
            Fill value for interpolator when outside range, by default np.nan.
        bounds_error : bool, optional
            Whether to raise an exception when outside range, by default False.
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
            except Exception:
                # Keep behaviour of earlier code but surface the failure
                raise

    def __call__(self, depth: npt.ArrayLike, cols=None) -> pd.DataFrame:
        """Interpolate and return requested columns for provided depths."""
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
