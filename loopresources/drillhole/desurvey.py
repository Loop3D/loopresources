"""Desurvey utilities for drillhole survey manipulation.

Functions to convert survey azimuth/inclination records into XYZ coordinates
sampled at a regular interval along a drillhole trace.
"""
import pandas as pd
import numpy as np

from .dhconfig import DhConfig
from .math import slerp, vector2trendandplunge, trendandplunge2vector


def desurvey(
    collar: pd.DataFrame, survey: pd.DataFrame, newinterval=10, method="minimum_curvature", drop_intermediate=True
) -> pd.DataFrame:
    """Compute well path from collar and survey data at regular intervals.

    Parameters:
        collar (pd.DataFrame): DataFrame containing collar information with
            columns defined in DhConfig.
        survey (pd.DataFrame): DataFrame containing survey information with
            columns defined in DhConfig.
        newinterval (float): Interval at which to resample the drillhole trace.
        method (str): Method to use for desurveying. Options are
            "tangent" or "minimum_curvature".
        drop_intermediate (bool): Whether to drop intermediate calculation
            columns from the output DataFrame.
    Returns:    
        pd.DataFrame: Resampled drillhole trace with XYZ coordinates and
            survey information at specified intervals.

    Notes:
        - The "tangent" method uses linear interpolation between survey points.
        - The "minimum_curvature" method uses spherical linear interpolation
          (SLERP) for a smoother path.
        - If there are insufficient survey points, the function will default to
          the tangent method.
    """
    if newinterval <= 0:
        raise ValueError("newinterval must be a positive value.")
    if not isinstance(survey, pd.DataFrame):
        return pd.DataFrame()
    if len(survey) == 0 or collar.empty:
        return pd.DataFrame()
    survey = survey.sort_values(by=DhConfig.depth).reset_index(drop=True)
    if len(survey) < 2:
        return straight_path_from_single_survey(collar, survey, newinterval)
    if method == "tangent":
        return tangent_method(collar, survey, newinterval, drop_intermediate)
    
    elif method == "minimum_curvature":
        return minimum_curvature(collar, survey, newinterval, drop_intermediate)
    else:
        raise ValueError(f"Unknown method: {method}")


def tangent_method(
        collar: pd.DataFrame, survey: pd.DataFrame, newinterval=10, drop_intermediate=True
) -> pd.DataFrame:
    """Compute well path using tangent method at regular intervals."""
    # Implementation goes here
    if not hasattr(newinterval, "__len__"):  # is it an array?
        newdepth = np.arange(
            0,
            collar[DhConfig.total_depth].max(),
            newinterval,
        )
    else:
        newdepth = newinterval
    depth = survey[DhConfig.depth].values
    azimuth = survey[DhConfig.azimuth].values
    dip = survey[DhConfig.dip].values
    vertices = [[collar[DhConfig.x].values[0], collar[DhConfig.y].values[0], collar[DhConfig.z].values[0]]]
    for i in range(0, len(survey)):
        newpos =vertices[-1][:]
        delta_depth = depth[i] - depth[i - 1]
        newpos[0] += delta_depth * np.sin(np.deg2rad(90 - dip[i - 1])) * np.sin(np.deg2rad(azimuth[i - 1]))
        newpos[1] += delta_depth * np.sin(np.deg2rad(90 - dip[i - 1])) * np.cos(np.deg2rad(azimuth[i - 1]))
        newpos[2] += delta_depth * np.cos(np.deg2rad(90 - dip[i - 1]))
        vertices.append(newpos)
    vertices = np.array(vertices)
    seg_vecs = np.diff(vertices, axis=0)  # segment vectors
    seg_lens = np.linalg.norm(seg_vecs, axis=1)     # segment lengths
    # cumulative length along the polyline
    cumlen = np.concatenate(([0], np.cumsum(seg_lens)))
    seg_idx = np.searchsorted(cumlen, newdepth, side="right") - 1
    seg_idx = np.clip(seg_idx, 0, len(seg_vecs) - 1)
    # local distance inside each segment
    seg_start_s = cumlen[seg_idx]
    local_s = newdepth - seg_start_s
    t = local_s / seg_lens[seg_idx]                 # interpolation factor 0–1

    # interpolate points
    points = vertices[seg_idx] + seg_vecs[seg_idx] * t[:, None]
    return points


def straight_path_from_single_survey(collar, survey, newinterval=10):
    """Compute straight drillhole path from collar and one survey station, resampled at regular intervals."""
    # Extract collar coordinates
    depth = survey[DhConfig.depth]

    if not hasattr(newinterval, "__len__"):  # is it an array?
        newdepth = np.arange(
            0,
            collar[DhConfig.total_depth].max(),
            newinterval,
        )
    else:
        newdepth = newinterval
    new_trend = [survey[DhConfig.azimuth].to_list()[0]] * len(newdepth)
    new_plunge = [survey[DhConfig.dip].to_list()[0]] * len(newdepth)
    resampled_survey = pd.DataFrame(
        np.vstack([newdepth, new_trend, new_plunge]).T,
        columns=[DhConfig.depth, DhConfig.azimuth, DhConfig.dip],
    )
    trend = survey[DhConfig.azimuth].values[0]  # .apply(math.radians)
    plunge = survey[DhConfig.dip].values[0]  # + #.apply(math.radians)
    unit_vector = trendandplunge2vector(
        [trend],[plunge])
    dx = newdepth*unit_vector[0,0]
    dy = newdepth*unit_vector[0,1]
    dz = newdepth*unit_vector[0,2]

    resampled_survey["xm"] = dx
    resampled_survey["ym"] = dy
    resampled_survey["zm"] = dz
    resampled_survey["x_from"] = resampled_survey["xm"] + collar[DhConfig.x].values[0]
    resampled_survey["y_from"] = resampled_survey["ym"] + collar[DhConfig.y].values[0]
    resampled_survey["z_from"] = -resampled_survey["zm"] + collar[DhConfig.z].values[0]
    resampled_survey["x_to"] = resampled_survey["xm"] + collar[DhConfig.x].values[0] + newinterval
    resampled_survey["y_to"] = resampled_survey["ym"] + collar[DhConfig.y].values[0] + newinterval
    resampled_survey["z_to"] = -resampled_survey["zm"] + collar[DhConfig.z].values[0] - newinterval
    resampled_survey["x_mid"] = (
        resampled_survey["xm"] + collar[DhConfig.x].values[0] + 0.5 * newinterval
    )
    resampled_survey["y_mid"] = (
        resampled_survey["ym"] + collar[DhConfig.y].values[0] + 0.5 * newinterval
    )
    resampled_survey["z_mid"] = (
        -resampled_survey["zm"] + collar[DhConfig.z].values[0] - 0.5 * newinterval
    )
    resampled_survey["x"] = resampled_survey["x_mid"]
    resampled_survey["y"] = resampled_survey["y_mid"]
    resampled_survey["z"] = resampled_survey["z_mid"]
    return resampled_survey.drop(columns=["xm", "ym", "zm"])


def minimum_curvature(
    collar: pd.DataFrame, survey: pd.DataFrame, newinterval=10, drop_intermediate=True
) -> pd.DataFrame:
    """Compute well path using SLERP-based integration at regular intervals."""
    # Convert degrees to radians
    trend = survey[DhConfig.azimuth].values  # .apply(math.radians)
    plunge = survey[DhConfig.dip].values  # + #.apply(math.radians)

    if not hasattr(newinterval, "__len__"):  # is it an array?
        newdepth = np.arange(
            0,
            collar[DhConfig.total_depth].max(),
            newinterval,
        )
    else:
        newdepth = newinterval
    unit_vectors = trendandplunge2vector(trend, plunge)
    new_vectors = slerp(unit_vectors, survey[DhConfig.depth].values, newdepth)
    new_trend, new_plunge = vector2trendandplunge(new_vectors)
    # Assume plunge is defined as negative down
    # Convert to inclination as angle from vertical 0 being down
    new_inclination = np.deg2rad(90) + new_plunge
    
    resampled_survey = pd.DataFrame(
        np.vstack([newdepth, new_trend, new_plunge]).T,
        columns=[DhConfig.depth, DhConfig.azimuth, DhConfig.dip],
    )

    resampled_survey["xm"] = 0.0
    resampled_survey["ym"] = 0.0
    resampled_survey["zm"] = 0.0
    mask = np.vstack(
        [
            np.arange(0, resampled_survey.shape[0] - 1),
            np.arange(1, resampled_survey.shape[0]),
        ]
    ).T
    i1 = new_inclination[mask[:, 0]]
    i2 = new_inclination[mask[:, 1]]
    a1 = new_trend[mask[:, 0]]
    a2 = new_trend[mask[:, 1]]
    # distance between the two points
    CL = (
        resampled_survey.loc[mask[:, 1], DhConfig.depth].to_numpy()
        - resampled_survey.loc[mask[:, 0], DhConfig.depth].to_numpy()
    )
    # dog leg factor
    DL = np.arccos(np.cos(i2 - i1) - (np.sin(i1) * np.sin(i2)) * (1 - np.cos(a2 - a1)))
    RF = np.ones_like(DL)
    # when dog leg is 0 the correction factor RF is 1.0
    RF[DL != 0.0] = np.tan(DL[DL != 0.0] / 2) * (2 / DL[DL != 0.0])
    # find the set distance in E/W
    resampled_survey.loc[mask[:, 1], "xm"] = (
        (np.sin(i1) * np.sin(a1)) + (np.sin(i2) * np.sin(a2))
    ) * (RF * (CL / 2))
    # find the set distance in N/S
    resampled_survey.loc[mask[:, 1], "ym"] = (
        (np.sin(i1) * np.cos(a1)) + (np.sin(i2) * np.cos(a2))
    ) * (RF * (CL / 2))
    # find the set distance in vertical
    resampled_survey.loc[mask[:, 1], "zm"] = (np.cos(i1) + np.cos(i2)) * (CL / 2) * RF
    # create an array of cumulative distances to calculate the new coordinates
    resampled_survey["xm"] = resampled_survey["xm"].cumsum()
    resampled_survey["ym"] = resampled_survey["ym"].cumsum()
    resampled_survey["zm"] = resampled_survey["zm"].cumsum()
    resampled_survey["x_from"] = resampled_survey["xm"] + collar[DhConfig.x].values[0]
    resampled_survey["y_from"] = resampled_survey["ym"] + collar[DhConfig.y].values[0]
    resampled_survey["z_from"] = resampled_survey["zm"] + collar[DhConfig.z].values[0]
    resampled_survey["x_to"] = resampled_survey["xm"] + collar[DhConfig.x].values[0] + newinterval
    resampled_survey["y_to"] = resampled_survey["ym"] + collar[DhConfig.y].values[0] + newinterval
    resampled_survey["z_to"] = resampled_survey["zm"] + collar[DhConfig.z].values[0] - newinterval
    resampled_survey["x_mid"] = (
        resampled_survey["xm"] + collar[DhConfig.x].values[0] + 0.5 * newinterval
    )
    resampled_survey["y_mid"] = (
        resampled_survey["ym"] + collar[DhConfig.y].values[0] + 0.5 * newinterval
    )
    resampled_survey["z_mid"] = (
        -resampled_survey["zm"] + collar[DhConfig.z].values[0] - 0.5 * newinterval
    )
    resampled_survey["x"] = resampled_survey["x_mid"]
    resampled_survey["y"] = resampled_survey["y_mid"]
    resampled_survey["z"] = resampled_survey["z_mid"]
    resampled_survey[DhConfig.azimuth] = np.rad2deg(new_trend) % 360
    resampled_survey[DhConfig.dip] = np.rad2deg(new_plunge)
    if drop_intermediate:
        return resampled_survey.drop(columns=["xm", "ym", "zm"])
    else:
        return resampled_survey
