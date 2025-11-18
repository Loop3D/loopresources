"""Orientation utilities for converting alpha/beta/gamma core angles into vectors."""

import numpy as np
import pandas as pd

from loopresources.drillhole.dhconfig import DhConfig


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
    """Calculate the lineation vector and plane from core orientation angles."""
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
    inplace=False,
) -> pd.DataFrame:
    """Calculate the plane vector from core orientation angles.

    Parameters
    ----------
    df : pd.DataFrame
        Dataframe containing the orientation data.
    column_map : dict, optional
        Mapping of expected columns to dataframe column names.
    inplace : bool, optional
        If True, modify the dataframe in place.
    Returns
    -------
    pd.DataFrame
        Dataframe with added 'nx', 'ny', 'nz' columns representing the normal vector.
    Notes
    -----
        The input angles are expected to be in degrees.
    """
    if not inplace:
        df = df.copy()
    plane_local = np.zeros((len(df), 3))
    plane_local[:, 0] = np.cos(np.deg2rad(df[DhConfig.beta])) * np.cos(
        np.deg2rad(df[DhConfig.alpha])
    )
    plane_local[:, 1] = np.sin(np.deg2rad(df[DhConfig.beta])) * np.cos(
        np.deg2rad(df[DhConfig.alpha])
    )
    plane_local[:, 2] = np.sin(np.deg2rad(df[DhConfig.alpha]))

    Z_rot = np.zeros((len(df), 3, 3))
    Y_rot = np.zeros((len(df), 3, 3))

    Y_rot[:, 0, 0] = np.cos(np.deg2rad(90 + df[DhConfig.dip]))
    Y_rot[:, 2, 0] = -np.sin(np.deg2rad(90 + df[DhConfig.dip]))
    Y_rot[:, 1, 1] = 1
    Y_rot[:, 0, 2] = np.sin(np.deg2rad(90 + df[DhConfig.dip]))
    Y_rot[:, 2, 2] = np.cos(np.deg2rad(90 + df[DhConfig.dip]))

    Z_rot[:, 0, 0] = np.cos(np.deg2rad(90 - df[DhConfig.azimuth]))
    Z_rot[:, 0, 1] = -np.sin(np.deg2rad(90 - df[DhConfig.azimuth]))
    Z_rot[:, 1, 0] = np.sin(np.deg2rad(90 - df[DhConfig.azimuth]))
    Z_rot[:, 1, 1] = np.cos(np.deg2rad(90 - df[DhConfig.azimuth]))
    Z_rot[:, 2, 2] = 1
    plane = plane_local[:, :, None]
    vector = Z_rot @ Y_rot @ plane
    df["nx"] = vector[:, 0, 0]
    df["ny"] = vector[:, 1, 0]
    df["nz"] = vector[:, 2, 0]

    return df
