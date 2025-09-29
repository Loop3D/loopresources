import numpy as np
import pandas as pd
from LoopStructural.utils import normal_vector_to_strike_and_dip


def alphaBetaGamma2vector(
    df: pd.DataFrame,
    column_map={
        "Beta": "BetaAngle",
        "Alpha": "AlphaAngle",
        "DIP": "DIP_DEG",
        "AZIMUTH": "AZIMUTH_DEG",
        "Gamma": "Gamma",
    },
    inplace=False,
) -> pd.DataFrame:
    """Calculate the lineation vector and the plane from the alpha beta and gamma angle and core orientation

    Parameters
    ----------
    df : pd.DataFrame
        dataframe containing the orientation data
    column_map : dict, optional
        m, by default { 'Beta': 'BetaAngle', 'Alpha': 'AlphaAngle', 'DIP': 'DIP_DEG', 'AZIMUTH': 'AZIMUTH_DEG', 'Gamma': 'Gamma', }
    inplace : bool, optional
        Whether to modify the dataframe in place or create a copy, by default False
    Returns
    -------
    pd.DataFrame
        Original dataframe with the lineation vector and plane normal vector
    """
    if not inplace:
        df = df.copy()
    plane_local = np.zeros((len(df), 3))
    plane_local[:, 0] = np.cos(np.deg2rad(df[column_map["Beta"]])) * np.cos(
        np.deg2rad(df[column_map["Alpha"]])
    )
    plane_local[:, 1] = np.sin(np.deg2rad(df[column_map["Beta"]])) * np.cos(
        np.deg2rad(df[column_map["Alpha"]])
    )
    plane_local[:, 2] = np.sin(np.deg2rad(df[column_map["Alpha"]]))
    line_local = np.zeros((len(df), 3))
    line_local[:, 0] = np.cos(
        np.deg2rad(df[column_map["Beta"]] + df[column_map["Gamma"]])
    ) * np.sin(np.deg2rad(df[column_map["Alpha"]]))
    line_local[:, 1] = np.sin(
        np.deg2rad(df[column_map["Beta"]] + df[column_map["Gamma"]])
    ) * np.sin(np.deg2rad(df[column_map["Alpha"]]))
    line_local[:, 2] = np.cos(-np.deg2rad(df[column_map["Alpha"]]))
    Z_rot = np.zeros((len(df), 3, 3))
    Y_rot = np.zeros((len(df), 3, 3))

    Y_rot[:, 0, 0] = np.cos(np.deg2rad(90 + df[column_map["DIP"]]))
    Y_rot[:, 2, 0] = -np.sin(np.deg2rad(90 + df[column_map["DIP"]]))
    Y_rot[:, 1, 1] = 1
    Y_rot[:, 0, 2] = np.sin(np.deg2rad(90 + df[column_map["DIP"]]))
    Y_rot[:, 2, 2] = np.cos(np.deg2rad(90 + df[column_map["DIP"]]))

    Z_rot[:, 0, 0] = np.cos(np.deg2rad(90 - df[column_map["AZIMUTH"]]))
    Z_rot[:, 0, 1] = -np.sin(np.deg2rad(90 - df[column_map["AZIMUTH"]]))
    Z_rot[:, 1, 0] = np.sin(np.deg2rad(90 - df[column_map["AZIMUTH"]]))
    Z_rot[:, 1, 1] = np.cos(np.deg2rad(90 - df[column_map["AZIMUTH"]]))
    Z_rot[:, 2, 2] = 1
    line = line_local[:, :, None]
    line = Z_rot @ Y_rot @ line
    plane = plane_local[:, :, None]
    plane = Z_rot @ Y_rot @ plane
    df["nx"] = plane[:, 0, 0]
    df["ny"] = plane[:, 1, 0]
    df["nz"] = plane[:, 2, 0]
    df["lx"] = line[:, 0, 0]
    df["ly"] = line[:, 1, 0]
    df["lz"] = line[:, 2, 0]
    return df


def alphaBeta2vector(
    df: pd.DataFrame,
    column_map={
        "Beta": "BetaAngle",
        "Alpha": "AlphaAngle",
        "DIP": "DIP_DEG",
        "AZIMUTH": "AZIMUTH_DEG",
    },
    inplace=False,
    strike_dip=False,
):
    """Calculate the lineation vector from the alpha beta and gamma angle and core orientation

    Parameters
    ----------
    df : pd.DataFrame
        dataframe containing the orientation data
    column_map : dict, optional
        m, by default { 'Beta': 'BetaAngle', 'Alpha': 'AlphaAngle', 'DIP': 'DIP_DEG', 'AZIMUTH': 'AZIMUTH_DEG' }

    Returns
    -------
    pd.DataFrame
        the original dataframe with the plane vector added
    """
    if not inplace:
        df = df.copy()
    plane_local = np.zeros((len(df), 3))
    plane_local[:, 0] = np.cos(np.deg2rad(df[column_map["Beta"]])) * np.cos(
        np.deg2rad(df[column_map["Alpha"]])
    )
    plane_local[:, 1] = np.sin(np.deg2rad(df[column_map["Beta"]])) * np.cos(
        np.deg2rad(df[column_map["Alpha"]])
    )
    plane_local[:, 2] = np.sin(np.deg2rad(df[column_map["Alpha"]]))

    Z_rot = np.zeros((len(df), 3, 3))
    Y_rot = np.zeros((len(df), 3, 3))

    Y_rot[:, 0, 0] = np.cos(np.deg2rad(90 + df[column_map["DIP"]]))
    Y_rot[:, 2, 0] = -np.sin(np.deg2rad(90 + df[column_map["DIP"]]))
    Y_rot[:, 1, 1] = 1
    Y_rot[:, 0, 2] = np.sin(np.deg2rad(90 + df[column_map["DIP"]]))
    Y_rot[:, 2, 2] = np.cos(np.deg2rad(90 + df[column_map["DIP"]]))

    Z_rot[:, 0, 0] = np.cos(np.deg2rad(90 - df[column_map["AZIMUTH"]]))
    Z_rot[:, 0, 1] = -np.sin(np.deg2rad(90 - df[column_map["AZIMUTH"]]))
    Z_rot[:, 1, 0] = np.sin(np.deg2rad(90 - df[column_map["AZIMUTH"]]))
    Z_rot[:, 1, 1] = np.cos(np.deg2rad(90 - df[column_map["AZIMUTH"]]))
    Z_rot[:, 2, 2] = 1
    plane = plane_local[:, :, None]
    vector = Z_rot @ Y_rot @ plane
    df["nx"] = vector[:, 0, 0]
    df["ny"] = vector[:, 1, 0]
    df["nz"] = vector[:, 2, 0]
    strike_dip = normal_vector_to_strike_and_dip(df[["nx", "ny", "nz"]].values)
    df["strike"] = strike_dip[:, 0]
    df["dip"] = strike_dip[:, 1]

    return df
