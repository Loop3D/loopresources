import numpy as np
import pandas as pd
from scipy.interpolate import interp1d
from typing import Union
from . import DhConfig


def desurvey(
    collar: pd.DataFrame,
    survey: pd.DataFrame,
    newinterval: Union[np.ndarray, float] = 1.0,
):
    """Desurvey and resample a drillhole along a specific interval

    Parameters
    ----------
    collar : pd.DataFrame
        collar for a single drill hole
    survey : pd.DataFrame
        survey table for a single drill hole
    newinterval : float, optional
        step size of interval, by default 1.0 meter

    Returns
    -------
    pd.DataFrame
        resulting table sampled along drillhole at the specific interval

    Notes
    -----
    This function uses the minimum curvature method for desurveying the drillhole.
    The azimuth and inclination of the drillhole are interpolated first to the new
    interval and then the xyz coordinates are calculated using the minimum curvature
    method

    """
    # print(collar[DhConfig.z].min(), collar[DhConfig.total_depth].max())
    if not hasattr(newinterval, "__len__"):  # is it an array?
        newdepth = np.arange(
            0,
            collar[DhConfig.total_depth].max(),
            newinterval,
        )
    else:
        newdepth = newinterval
    survey = survey.sort_values(DhConfig.depth).reset_index()
    if len(survey) == 0:
        raise ValueError("Survey table is empty")
    ## extrapolate using the bottom azimuth value.. its better than nothing
    # convert from dip to inclination
    # dip is measured from the horizontal, inclination is measured from the vertical
    # if positive dip down, then inclination = 90 - dip
    # if negative dip down, then inclination = 90 + dip
    # if inclination is provided not dip do nothing
    incl = survey[DhConfig.dip].to_numpy() + np.deg2rad(90)
    if not DhConfig.positive_dips_down:
        print("positive dips down")
        incl = np.deg2rad(90) - survey[DhConfig.dip].to_numpy()
    if DhConfig.dip_is_inclination:
        print("dip is inclination")
        incl = survey[DhConfig.dip].to_numpy()
    incl_fill_value = incl.tolist()[-1]
    azi_fill_value = survey[DhConfig.azimuth].to_list()[-1]
    # print(survey[DhConfig.depth])

    if survey.shape[0] > 1:
        azi_interp = interp1d(
            survey[DhConfig.depth].to_numpy(),
            survey[DhConfig.azimuth].to_numpy(),
            fill_value=azi_fill_value,
            bounds_error=False,
        )

        incli_interp = interp1d(
            survey[DhConfig.depth].to_numpy(),
            incl,
            fill_value=incl_fill_value,
            bounds_error=False,
        )
        azi = azi_interp(newdepth)
        incli = incli_interp(newdepth)
    else:
        azi = np.zeros_like(newdepth) + azi_fill_value
        incli = np.zeros_like(newdepth) + incl_fill_value

    resampled_survey = pd.DataFrame(
        np.vstack([newdepth, incli, azi]).T,
        columns=[DhConfig.depth, DhConfig.dip, DhConfig.azimuth],
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
    i1 = resampled_survey.loc[mask[:, 0], DhConfig.dip].to_numpy()
    i2 = resampled_survey.loc[mask[:, 1], DhConfig.dip].to_numpy()
    a1 = resampled_survey.loc[mask[:, 0], DhConfig.azimuth].to_numpy()
    a2 = resampled_survey.loc[mask[:, 1], DhConfig.azimuth].to_numpy()
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
    return resampled_survey
