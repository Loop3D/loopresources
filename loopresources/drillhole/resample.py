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
            if table[col].dtype == "object" or pd.api.types.is_string_dtype(table[col]):
                r[col] = None
            else:
                r[col] = np.nan

            # find values in the intervals and assign them to the survey
            r.loc[r.index[i], col] = table.loc[table.index[j], col].to_numpy()
            if len(exact_from[0]) > 0:
                r.loc[r.index[exact_from[0]], col] = table.loc[
                    table.index[exact_from[1]], col
                ].to_numpy()
            if len(exact_to[0]) > 0:
                r.loc[r.index[exact_to[0]], col] = table.loc[
                    table.index[exact_to[1]], col
                ].to_numpy()
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
    result = pd.DataFrame(
        {
            DhConfig.sample_from: new_from,
            DhConfig.sample_to: new_to,
        }
    )

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
            overlap_mask = (table[DhConfig.sample_from] < new_t) & (
                table[DhConfig.sample_to] > new_f
            )
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


def merge_interval_tables(tables: List[pd.DataFrame]) -> pd.DataFrame:
    """
    Merge multiple interval tables into a single table by splitting intervals
    at every boundary present in any input table.

    The resulting table contains atomic, non-overlapping intervals covering
    the union of the input intervals for each hole. Columns from input tables
    are preserved; if the same column name appears in multiple input tables
    the later occurrences are renamed with a suffix "_N" to avoid collisions.

    Parameters
    ----------
    tables : list of pd.DataFrame
        List of interval tables to merge. Each table must contain the
        required columns: DhConfig.holeid, DhConfig.sample_from, DhConfig.sample_to.

    Returns
    -------
    pd.DataFrame
        Merged interval table with columns from all inputs and added
        DhConfig.depth_mid.
    """
    # If no tables provided return an empty canonical dataframe
    if not tables:
        return pd.DataFrame(
            columns=[DhConfig.holeid, DhConfig.sample_from, DhConfig.sample_to, DhConfig.depth_mid]
        )

    # Validate required columns exist in at least one table
    required = {DhConfig.holeid, DhConfig.sample_from, DhConfig.sample_to}

    # Prepare tables: copy and normalize column names to avoid collisions
    processed_tables = []
    col_counts = {}
    for ti, tab in enumerate(tables, start=1):
        t = tab.copy()
        if not required.issubset(set(t.columns)):
            raise ValueError(f"Table {ti} is missing required columns: {required - set(t.columns)}")

        # Rename data columns that would collide with previously seen names
        rename_map = {}
        for c in t.columns:
            if c in required:
                continue
            count = col_counts.get(c, 0)
            if count == 0:
                # first occurrence - keep name
                col_counts[c] = 1
            else:
                # subsequent occurrence - rename with suffix
                col_counts[c] = count + 1
                new_name = f"{c}_{col_counts[c]}"
                rename_map[c] = new_name
        if rename_map:
            t = t.rename(columns=rename_map)
        processed_tables.append(t)

    # Gather all hole ids across tables
    hole_ids = set()
    for t in processed_tables:
        hole_ids.update(t[DhConfig.holeid].unique())

    merged_rows = []

    # Process each hole independently
    for hole in sorted(hole_ids):
        # collect all unique boundaries for this hole
        boundaries = set()
        for t in processed_tables:
            sub = t[t[DhConfig.holeid] == hole]
            if sub.empty:
                continue
            boundaries.update(sub[DhConfig.sample_from].tolist())
            boundaries.update(sub[DhConfig.sample_to].tolist())
        if not boundaries:
            continue
        sorted_bounds = sorted(boundaries)

        # build atomic segments between consecutive boundaries
        for a, b in zip(sorted_bounds[:-1], sorted_bounds[1:]):
            if b <= a:
                continue
            row = {
                DhConfig.holeid: hole,
                DhConfig.sample_from: a,
                DhConfig.sample_to: b,
            }

            # For each processed table, find the interval that covers [a,b]
            for t in processed_tables:
                sub = t[t[DhConfig.holeid] == hole]
                if sub.empty:
                    continue
                cover = sub[(sub[DhConfig.sample_from] <= a) & (sub[DhConfig.sample_to] >= b)]
                if cover.empty:
                    # no covering interval -> leave values as NaN
                    continue
                # If multiple matches take the first (shouldn't happen if inputs valid)
                cover_row = cover.iloc[0]
                for c in cover_row.index:
                    if c in {DhConfig.holeid, DhConfig.sample_from, DhConfig.sample_to}:
                        continue
                    # only set value if not already present (earlier table wins for same-named column)
                    if c not in row:
                        row[c] = cover_row[c]
            merged_rows.append(row)

    if not merged_rows:
        return pd.DataFrame(columns=[DhConfig.holeid, DhConfig.sample_from, DhConfig.sample_to])

    result = pd.DataFrame(merged_rows)
    # Ensure columns order: identifiers then data
    id_cols = [DhConfig.holeid, DhConfig.sample_from, DhConfig.sample_to]
    other_cols = [c for c in result.columns if c not in id_cols]
    result = result[id_cols + other_cols]
    # sort and reset index
    result = result.sort_values([DhConfig.holeid, DhConfig.sample_from]).reset_index(drop=True)
    return result
