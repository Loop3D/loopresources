import numpy as np
import pandas as pd
from scipy.interpolate import interp1d
import pytest

from loopresources.drillhole.dhconfig import DhConfig
from loopresources.drillhole.drillhole import DrillHoleTrace


def make_simple_trace():
    # Create a simple straight trace: depth 0..10, z = 100 - depth, x=y=0
    depths = np.arange(0.0, 11.0, 1.0)
    x = np.zeros_like(depths)
    y = np.zeros_like(depths)
    z = 100.0 - depths

    pts = pd.DataFrame(
        {
            DhConfig.depth: depths,
            "x": x,
            "y": y,
            "z": z,
        }
    )

    # Construct DrillHoleTrace without using desurvey by creating object and setting attributes
    trace = DrillHoleTrace.__new__(DrillHoleTrace)
    trace.trace_points = pts
    trace.x_interpolator = interp1d(
        pts[DhConfig.depth].values, pts["x"].values, fill_value="extrapolate"
    )
    trace.y_interpolator = interp1d(
        pts[DhConfig.depth].values, pts["y"].values, fill_value="extrapolate"
    )
    trace.z_interpolator = interp1d(
        pts[DhConfig.depth].values, pts["z"].values, fill_value="extrapolate"
    )

    return trace


def test_find_intersection_vectorized():
    trace = make_simple_trace()

    # plane at z = 95 => intersection at depth 5
    def plane(coords):
        # coords is Nx3 (x,y,z)
        return coords[:, 2] - 95.0

    df = trace.find_implicit_function_intersection(plane)

    assert isinstance(df, pd.DataFrame)
    assert len(df) == 1
    assert pytest.approx(df.loc[0, DhConfig.depth]) == 5.0
    assert pytest.approx(df.loc[0, "z"]) == 95.0
    assert pytest.approx(df.loc[0, "x"]) == 0.0
    assert pytest.approx(df.loc[0, "y"]) == 0.0


def test_find_intersection_separate_args():
    trace = make_simple_trace()

    # plane at z = 98 => intersection at depth 2
    def plane_x_y_z(x, y, z):
        return z - 98.0

    df = trace.find_implicit_function_intersection(plane_x_y_z)

    assert isinstance(df, pd.DataFrame)
    assert len(df) == 1
    assert pytest.approx(df.loc[0, DhConfig.depth]) == 2.0
    assert pytest.approx(df.loc[0, "z"]) == 98.0


def test_no_intersection_returns_empty():
    trace = make_simple_trace()

    # function that never crosses zero (always positive)
    def always_positive(coords):
        return np.ones((len(coords),)) * 5.0

    df = trace.find_implicit_function_intersection(always_positive)
    assert isinstance(df, pd.DataFrame)
    assert df.empty
