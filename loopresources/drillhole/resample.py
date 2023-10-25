from hmac import new
from . import DhConfig
from . import DataFrameInterpolator
import numpy as np
import pandas as pd
import logging
from scipy.interpolate import interp1d

from .. import PRIVATE_DEPTH

logger = logging.getLogger(__name__)


def resample_point(
    r: pd.DataFrame,
    table: pd.DataFrame,
    cols: list,
    method="direct",
    inplace: bool = False,
):
    """
    Composite a table to a survey
    """
    if table.empty:
        logger.debug("Warning: table is empty, nothing has been resampled")
        return r
    if not inplace:
        r = r.copy()
    if method == "direct":
        # interval sampling, if the new depth marker falls in the interval
        # then that value is used. Useful for discrete variables

        ## TODO what if the point is on the the marker?
        i, j = np.where(
            np.logical_and(
                table[DhConfig.sample_from].to_numpy()[None, :]
                <= r[DhConfig.depth].to_numpy()[:, None],
                table[DhConfig.sample_to].to_numpy()[None, :]
                > r[DhConfig.depth].to_numpy()[:, None],
            )
        )
        exact_from = np.where(
            table[DhConfig.sample_from].to_numpy()[None, :]
            == r[DhConfig.depth].to_numpy()[:, None]
        )
        exact_to = np.where(
            table[DhConfig.sample_to].to_numpy()[None, :]
            == r[DhConfig.depth].to_numpy()[:, None]
        )
        cols_in = [col for col in cols if col in table.columns]
        r[cols_in] = np.nan
        r.loc[r.index[i], cols_in] = table.loc[table.index[j], cols_in].to_numpy()
        # for col in cols:
        #     if col not in table.columns:
        #         # warn the user
        #         print(f"Warning: {col} not in survey, skipping")
        #         continue
        #     r[col] = np.nan
        #     # find values in the intervals and assign them to the survey
        #     r.loc[r.index[i], col] = table.loc[table.index[j], col].to_numpy()
        # # r.loc[exact_from[0], col] = table.loc[
        # #     table.index[exact_from[1], col]
        # # ].to_numpy()
        # # r.loc[exact_to[0], col] = table.loc[
        # #     table.index[exact_to[1], col]
        # ].to_numpy()
    return r


def desurvey_point(
    r: pd.DataFrame,
    table: pd.DataFrame,
    cols: list,
    table_depth: str = "From",
):
    interpolator = DataFrameInterpolator(r, DhConfig.depth)
    desurvey = interpolator(table[table_depth], cols=cols).reset_index()
    merged = table.reset_index().merge(desurvey)
    merged = pd.concat([table.reset_index(), desurvey], axis=1)
    # print(desurvey, table.reset_index())
    print(merged.shape, desurvey.shape, table.shape)
    return merged


def resample_interval(
    r: pd.DataFrame,
    table: pd.DataFrame,
    cols: list,
    method="direct",
    inplace: bool = False,
):
    """
    Composite a table to a survey
    """
    if table.empty:
        print("Warning: table is empty, nothing has been resampled")
        return r
    if not inplace:
        r = r.copy()
    if method == "direct":
        # interval sampling, if the new depth marker falls in the interval
        # then that value is used. Useful for discrete variables

        ## TODO what if the point is on the the marker?
        i, j = np.where(
            np.logical_and(
                table[DhConfig.sample_from].to_numpy()[None, :]
                <= r[DhConfig.depth].to_numpy()[:, None],
                table[DhConfig.sample_to].to_numpy()[None, :]
                > r[DhConfig.depth].to_numpy()[:, None],
            )
        )
        exact_from = np.where(
            table[DhConfig.sample_from].to_numpy()[None, :]
            == r[DhConfig.depth].to_numpy()[:, None]
        )
        exact_to = np.where(
            table[DhConfig.sample_to].to_numpy()[None, :]
            == r[DhConfig.depth].to_numpy()[:, None]
        )
        for col in cols:
            if col not in table.columns:
                # warn the user
                print(f"Warning: {col} not in survey, skipping")
                continue
            r[col] = np.nan
            # find values in the intervals and assign them to the survey
            r.loc[r.index[i], col] = table.loc[table.index[j], col].to_numpy()
            r.loc[exact_from[0], col] = table.loc[
                table.index[exact_from[1], col]
            ].to_numpy()
            r.loc[exact_to[0], col] = table.loc[
                table.index[exact_to[1], col]
            ].to_numpy()
    return r
