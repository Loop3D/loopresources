from . import DhConfig
from . import DataFrameInterpolator
import numpy as np
import pandas as pd
import logging


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
        _exact_from = np.where(
            table[DhConfig.sample_from].to_numpy()[None, :] == r[DhConfig.depth].to_numpy()[:, None]
        )
        _exact_to = np.where(
            table[DhConfig.sample_to].to_numpy()[None, :] == r[DhConfig.depth].to_numpy()[:, None]
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


def desurvey_point(r: pd.DataFrame, table: pd.DataFrame, cols: list):
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
            table[DhConfig.sample_from].to_numpy()[None, :] == r[DhConfig.depth].to_numpy()[:, None]
        )
        exact_to = np.where(
            table[DhConfig.sample_to].to_numpy()[None, :] == r[DhConfig.depth].to_numpy()[:, None]
        )
        for col in cols:
            if col not in table.columns:
                # warn the user
                print(f"Warning: {col} not in survey, skipping")
                continue
            
            # Initialize column with appropriate type
            if table[col].dtype == 'object' or pd.api.types.is_string_dtype(table[col]):
                r[col] = None
            else:
                r[col] = np.nan
            
            # find values in the intervals and assign them to the survey
            r.loc[r.index[i], col] = table.loc[table.index[j], col].to_numpy()
            if len(exact_from[0]) > 0:
                r.loc[r.index[exact_from[0]], col] = table.loc[table.index[exact_from[1]], col].to_numpy()
            if len(exact_to[0]) > 0:
                r.loc[r.index[exact_to[0]], col] = table.loc[table.index[exact_to[1]], col].to_numpy()
    return r


def resample_interval_to_new_interval(
    table: pd.DataFrame,
    cols: list,
    new_interval: float = 1.0,
    method="mode",
):
    """
    Resample interval data to a new regular interval.
    
    For each new interval, finds all overlapping original intervals and 
    assigns the value that has the biggest occurrence (mode).
    
    Parameters
    ----------
    table : pd.DataFrame
        Interval table with FROM and TO columns
    cols : list
        List of column names to resample
    new_interval : float, default 1.0
        Size of new regular intervals
    method : str, default "mode"
        Method to use for aggregation. Currently only "mode" is supported,
        which selects the value with the biggest occurrence in each interval.
    
    Returns
    -------
    pd.DataFrame
        Resampled interval data with regular intervals and specified columns
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
    
    # Create result dataframe
    result = pd.DataFrame({
        DhConfig.sample_from: new_from,
        DhConfig.sample_to: new_to,
    })
    
    # Process each column
    for col in cols:
        if col not in table.columns:
            logger.warning(f"Warning: {col} not in table, skipping")
            continue
        
        result[col] = None
        
        # For each new interval, find overlapping original intervals
        for idx, (new_f, new_t) in enumerate(zip(new_from, new_to)):
            # Find overlapping intervals
            # An interval overlaps if: original_from < new_to AND original_to > new_from
            overlap_mask = (table[DhConfig.sample_from] < new_t) & (table[DhConfig.sample_to] > new_f)
            overlapping = table[overlap_mask]
            
            if len(overlapping) == 0:
                continue
            
            if method == "mode":
                # Calculate the length of overlap for each original interval
                overlap_lengths = []
                overlap_values = []
                
                for _, row in overlapping.iterrows():
                    orig_from = row[DhConfig.sample_from]
                    orig_to = row[DhConfig.sample_to]
                    
                    # Calculate overlap length
                    overlap_start = max(new_f, orig_from)
                    overlap_end = min(new_t, orig_to)
                    overlap_len = overlap_end - overlap_start
                    
                    overlap_lengths.append(overlap_len)
                    overlap_values.append(row[col])
                
                # Find value with maximum total occurrence (sum of overlap lengths)
                value_occurrences = {}
                for val, length in zip(overlap_values, overlap_lengths):
                    if val in value_occurrences:
                        value_occurrences[val] += length
                    else:
                        value_occurrences[val] = length
                
                # Select the value with maximum occurrence
                if value_occurrences:
                    max_value = max(value_occurrences, key=value_occurrences.get)
                    result.loc[idx, col] = max_value
    
    return result
