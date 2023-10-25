import numpy as np
import pandas as pd
from scipy.interpolate import interp1d
from . import DhConfig
from typing import Optional, List, Union


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
    ## extrapolate using the bottom azimuth value.. its better than nothing
    dip_fill_value = survey[DhConfig.dip].to_list()[-1]
    azi_fill_value = survey[DhConfig.azimuth].to_list()[-1]
    # if scipy.__version__ > "0.17.0":
    #     # if using newer scipy then we can use upper and lower values
    #     dip_fill_value = [
    #         survey[DhConfig.dip].to_list()[0],
    #         survey[DhConfig.dip].to_list()[-1],
    #     ]
    #     azi_fill_value = [
    #         survey[DhConfig.azimuth].to_list()[0],
    #         survey[DhConfig.azimuth].to_list()[-1],
    #     ]
    if survey.shape[0] > 1:
        azi_interp = interp1d(
            survey[DhConfig.depth].to_numpy(),
            survey[DhConfig.azimuth].to_numpy(),
            fill_value=azi_fill_value,
            bounds_error=False,
        )

        incli_interp = interp1d(
            survey[DhConfig.depth].to_numpy(),
            survey[DhConfig.dip].to_numpy(),
            fill_value=dip_fill_value,
            bounds_error=False,
        )
        azi = azi_interp(newdepth)
        incli = incli_interp(newdepth)
    else:
        azi = np.zeros_like(newdepth) + azi_fill_value
        incli = np.zeros_like(newdepth) + dip_fill_value

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
    CL = (
        resampled_survey.loc[mask[:, 1], DhConfig.depth].to_numpy()
        - resampled_survey.loc[mask[:, 0], DhConfig.depth].to_numpy()
    )

    DL = np.arccos(np.cos(i2 - i1) - (np.sin(i1) * np.sin(i2)) * (1 - np.cos(a2 - a1)))
    RF = np.ones_like(DL)
    RF[DL != 0.0] = np.tan(DL[DL != 0.0] / 2) * (2 / DL[DL != 0.0])
    resampled_survey.loc[mask[:, 1], "xm"] = (
        (np.sin(i1) * np.sin(a1)) + (np.sin(i2) * np.sin(a2))
    ) * (RF * (CL / 2))
    resampled_survey.loc[mask[:, 1], "ym"] = (
        (np.sin(i1) * np.cos(a1)) + (np.sin(i2) * np.cos(a2))
    ) * (RF * (CL / 2))
    resampled_survey.loc[mask[:, 1], "zm"] = (np.cos(i1) + np.cos(i2)) * (CL / 2) * RF
    resampled_survey["xm"] = resampled_survey["xm"].cumsum()
    resampled_survey["ym"] = resampled_survey["ym"].cumsum()
    resampled_survey["zm"] = resampled_survey["zm"].cumsum()
    resampled_survey["x_from"] = resampled_survey["xm"] + collar[DhConfig.x].values[0]
    resampled_survey["y_from"] = resampled_survey["ym"] + collar[DhConfig.y].values[0]
    resampled_survey["z_from"] = -resampled_survey["zm"] + collar[DhConfig.z].values[0]
    resampled_survey["x_to"] = (
        resampled_survey["xm"] + collar[DhConfig.x].values[0] + newinterval
    )
    resampled_survey["y_to"] = (
        resampled_survey["ym"] + collar[DhConfig.y].values[0] + newinterval
    )
    resampled_survey["z_to"] = (
        -resampled_survey["zm"] + collar[DhConfig.z].values[0] - newinterval
    )
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
