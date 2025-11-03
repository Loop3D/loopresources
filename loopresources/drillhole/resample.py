"""Utilities to resample and desurvey drillhole tables.

Provide helpers to resample point and interval tables to a survey
(e.g. mapping interval data to depths) and to desurvey interval/point
tables into a survey representation.
"""

from . import DhConfig
from . import DataFrameInterpolator
import numpy as np
import pandas as pd
import logging
from typing import List

logger = logging.getLogger(__name__)


def resample_point(
    r: pd.DataFrame,
    table: pd.DataFrame,
    cols: list,
    method="direct",
    inplace: bool = False,
):
    """Resample point/interval values from `table` onto survey `r`.

    Parameters
    ----------
    r : pd.DataFrame
        Survey dataframe containing a depth column named by
        ``DhConfig.depth``.
    table : pd.DataFrame
        Source table to sample from. Should include
        ``DhConfig.sample_from`` and ``DhConfig.sample_to`` columns for
        interval sampling.
    cols : list
        List of column names to resample from ``table`` onto ``r``.
    method : str, optional
        Sampling method to use. Only ``'direct'`` is currently supported.
    inplace : bool, optional
        If True, modify and return the input survey ``r``; otherwise a
        copy is returned.

    Returns
    -------
    pd.DataFrame
        Survey dataframe with the requested columns populated from
        ``table``.
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
        _exact_from = np.where(
            table[DhConfig.sample_from].to_numpy()[None, :] == r[DhConfig.depth].to_numpy()[:, None]
        )
        _exact_to = np.where(
            table[DhConfig.sample_to].to_numpy()[None, :] == r[DhConfig.depth].to_numpy()[:, None]
        )
        cols_in = [col for col in cols if col in table.columns]
        r[cols_in] = np.nan
        r.loc[r.index[i], cols_in] = table.loc[table.index[j], cols_in].to_numpy()
    return r


def desurvey_point(r: pd.DataFrame, table: pd.DataFrame, cols: list):
    """Desurvey values from a survey index into a table representation.

    This calls the DataFrameInterpolator to interpolate values from the
    survey ``r`` at depths given in ``table`` and returns the interpolated
    values concatenated with the original ``table``.

    Parameters
    ----------
    r : pd.DataFrame
        Survey dataframe used as source for interpolation.
    table : pd.DataFrame
        Target table containing depths at which values should be
        interpolated (uses ``DhConfig.depth``).
    cols : list
        Columns from ``r`` to interpolate.

    Returns
    -------
    pd.DataFrame
        Concatenation of ``table`` and the interpolated columns.
    """
    interpolator = DataFrameInterpolator(r, DhConfig.depth)
    desurvey = interpolator(table[DhConfig.depth], cols=cols)
    # merged = table.merge(desurvey)
    merged = pd.concat([table, desurvey], axis=1)
    # print(desurvey, table.reset_index())
    return merged


def resample_interval(
    r: pd.DataFrame,
    table: pd.DataFrame,
    cols: list,
    method="direct",
    inplace: bool = False,
):
    """Resample interval-valued columns from ``table`` onto survey ``r``.

    Parameters
    ----------
    r : pd.DataFrame
        Survey dataframe containing a depth column named by
        ``DhConfig.depth``.
    table : pd.DataFrame
        Interval table with ``DhConfig.sample_from`` and
        ``DhConfig.sample_to`` columns.
    cols : list
        Columns to resample.
    method : str, optional
        Sampling method to use. Only ``'direct'`` is currently supported.
    inplace : bool, optional
        If True, modify and return the input survey ``r``; otherwise a
        copy is returned.

    Returns
    -------
    pd.DataFrame
        Survey dataframe with interval-derived columns populated.
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
            table[DhConfig.sample_from].to_numpy()[None, :] == r[DhConfig.depth].to_numpy()[:, None]
        )
        exact_to = np.where(
            table[DhConfig.sample_to].to_numpy()[None, :] == r[DhConfig.depth].to_numpy()[:, None]
        )
        new_columns = {}
        for col in cols:
            if col not in table.columns:
                # warn the user
                print(f"Warning: {col} not in survey, skipping")
                continue

            # Initialize column with appropriate type
            if table[col].dtype == "object" or pd.api.types.is_string_dtype(table[col]):
                new_columns[col] = np.array([None] * len(r), dtype=object)
            else:
                new_columns[col] = np.array([np.nan] * len(r))

            # find values in the intervals and assign them to the survey
            new_columns[col][r.index[i]] = table.loc[table.index[j], col].to_numpy()
            if len(exact_from[0]) > 0:
                new_columns[col][exact_from[0]] = table.loc[
                    table.index[exact_from[1]], col
                ].to_numpy()
            if len(exact_to[0]) > 0:
                new_columns[col][exact_to[0]] = table.loc[table.index[exact_to[1]], col].to_numpy()
        new_df = pd.DataFrame(new_columns, index=r.index, columns=cols)
        r = pd.concat([r, new_df], axis=1)

    return r


def resample_interval_to_new_interval(
    table: pd.DataFrame,
    cols: list,
    new_interval: float = 1.0,
    method="mode",
):
    """Resample interval data to regular intervals and aggregate by overlap.

    For each new regular interval this function finds overlapping original
    intervals and assigns the value with the greatest total overlap
    (i.e. the maximum summed overlap length). Only the ``"mode"``
    aggregation method is currently supported.

    Parameters
    ----------
    table : pd.DataFrame
        Interval table with FROM and TO columns named by ``DhConfig``.
    cols : list
        Columns to resample.
    new_interval : float, optional
        Size of the new regular interval (default is 1.0).
    method : str, optional
        Aggregation method to use (default: ``"mode"``).

    Returns
    -------
    pd.DataFrame
        Resampled interval data with regular intervals and specified
        columns.
    """
    if table.empty:
        logger.debug("Warning: table is empty, nothing has been resampled")
        return pd.DataFrame()

    # Get the depth range
    min_depth = table[DhConfig.sample_from].min()
    max_depth = table[DhConfig.sample_to].max()

    # Create new regular intervals
    new_from = np.arange(min_depth, max_depth, new_interval)
    new_to = new_from + new_interval
    # Ensure last interval doesn't exceed max depth
    new_to = np.minimum(new_to, max_depth)
    # cols.pop(cols.index(DhConfig.sample_from))
    # cols.pop(cols.index(DhConfig.sample_to))
    # Create result dataframe
    result = pd.DataFrame(
        {
            DhConfig.sample_from: new_from,
            DhConfig.sample_to: new_to,
            **{col: [None] * len(new_from) for col in cols},
        }
    )

    
    grid = np.arange(0, 66, new_interval)  # 0 to 65
    grid_start = grid[:grid.shape[0]-1,None]
    grid_end = grid[1:,None]
    starts = table[DhConfig.sample_from].to_numpy()[None, :]
    ends = table[DhConfig.sample_to].to_numpy()[None, :]  
    in_interval = (grid_start >= starts) & (grid_end < ends)
    overlap_length = np.zeros_like(in_interval, dtype=float)
    overlap_length[in_interval] = new_interval
    start_only = (grid_start >= starts) & (grid_start < ends) & ~(grid_end <= ends)
    overlap_length[start_only] = (ends - grid_start)[start_only]
    end_only = (grid_end > starts) & (grid_end <= ends) & ~(grid_start >= starts)
    overlap_length[end_only] = (grid_end - starts)[end_only]
    if method == "mode":
        # interval with the longest overlap is equivalent to the mode
        # value for that interval
        segment_id = np.argmax(overlap_length, axis=1)
        result.loc[result.index[segment_id[0]],cols] = table.loc[table.index[segment_id[1]], cols].values
        # raise Exception("stop")
    result[DhConfig.holeid] = table[DhConfig.holeid].iloc[0]
    return result.copy()
