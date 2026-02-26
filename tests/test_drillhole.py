"""Tests for DrillHole sampling and plotting helpers."""

import numpy as np
import pandas as pd
import pytest

import matplotlib

matplotlib.use("Agg")

from loopresources.drillhole.drillhole_database import DrillholeDatabase
from loopresources.drillhole.dhconfig import DhConfig


@pytest.fixture
def sample_db():
    collar = pd.DataFrame(
        {
            DhConfig.holeid: ["DH001", "DH002"],
            DhConfig.x: [100.0, 200.0],
            DhConfig.y: [1000.0, 2000.0],
            DhConfig.z: [50.0, 60.0],
            DhConfig.total_depth: [10.0, 8.0],
        }
    )

    survey = pd.DataFrame(
        {
            DhConfig.holeid: ["DH001", "DH002"],
            DhConfig.depth: [0.0, 0.0],
            DhConfig.azimuth: [0.0, 0.0],
            DhConfig.dip: [90.0, 90.0],
        }
    )

    intervals = pd.DataFrame(
        {
            DhConfig.holeid: ["DH001", "DH001"],
            DhConfig.sample_from: [0.0, 5.0],
            DhConfig.sample_to: [5.0, 10.0],
            "LITHO": ["A", "B"],
            "GRADE": [1.0, 2.0],
        }
    )

    points = pd.DataFrame(
        {
            DhConfig.holeid: ["DH001", "DH001", "DH001"],
            DhConfig.depth: [1.0, 4.0, 9.0],
            "AU_PPM": [100.0, 200.0, 300.0],
        }
    )

    db = DrillholeDatabase(collar, survey)
    db.add_interval_table("geology", intervals)
    db.add_point_table("assay", points)
    return db


def test_downhole_depth_grid(sample_db):
    hole = sample_db["DH001"]
    grid = hole._downhole_depth_grid(step=2.5)
    np.testing.assert_allclose(grid, np.array([0.0, 2.5, 5.0, 7.5, 10.0]))

    empty = hole._downhole_depth_grid(step=1.0, max_depth=0.0)
    assert empty.size == 0

    with pytest.raises(ValueError, match="step must be > 0"):
        hole._downhole_depth_grid(step=0.0)


def test_sample_downhole_values_interval_categorical(sample_db):
    hole = sample_db["DH001"]
    depths, values = hole._sample_downhole_values("geology", "LITHO", 2.5, "categorical")
    np.testing.assert_allclose(depths, np.array([0.0, 2.5, 5.0, 7.5, 10.0]))
    assert values.tolist() == ["A", "A", "A", "B", "B"]


def test_sample_downhole_values_interval_numeric(sample_db):
    hole = sample_db["DH001"]
    depths, values = hole._sample_downhole_values("geology", "GRADE", 2.5, "image")
    np.testing.assert_allclose(depths, np.array([0.0, 2.5, 5.0, 7.5, 10.0]))
    np.testing.assert_allclose(values.astype(float), np.array([1.0, 1.0, 1.0, 2.0, 2.0]))


def test_sample_downhole_values_point_line(sample_db):
    hole = sample_db["DH001"]
    depths, values = hole._sample_downhole_values("assay", "AU_PPM", 1.0, "line")
    np.testing.assert_allclose(depths, np.array([1.0, 4.0, 9.0]))
    np.testing.assert_allclose(values, np.array([100.0, 200.0, 300.0]))


def test_sample_downhole_values_point_categorical_grid(sample_db):
    hole = sample_db["DH001"]
    depths, values = hole._sample_downhole_values("assay", "AU_PPM", 2.0, "categorical")
    np.testing.assert_allclose(depths, np.array([0.0, 2.0, 4.0, 6.0, 8.0, 10.0]))
    assert values.tolist() == [100.0, None, 200.0, None, 300.0, None]


def test_sample_downhole_values_missing_table_column(sample_db):
    hole = sample_db["DH001"]
    with pytest.raises(KeyError, match="Table 'missing' not found"):
        hole._sample_downhole_values("missing", "LITHO", 1.0, "line")

    with pytest.raises(KeyError, match="Column 'NOPE' not found in interval table"):
        hole._sample_downhole_values("geology", "NOPE", 1.0, "line")

    with pytest.raises(KeyError, match="Column 'NOPE' not found in point table"):
        hole._sample_downhole_values("assay", "NOPE", 1.0, "line")


def test_plot_downhole_multi_hole_layout_errors(sample_db):
    with pytest.raises(ValueError, match="ax must have at least one axis per hole"):
        sample_db.plot_downhole("geology", "LITHO", holes=["DH001", "DH002"], ax=[])

    with pytest.raises(ValueError, match="Unknown hole IDs"):
        sample_db.plot_downhole("geology", "LITHO", holes=["DH999"])

    with pytest.raises(ValueError, match="layout must be 'grid' or 'column'"):
        sample_db.plot_downhole("geology", "LITHO", layout="row")

    with pytest.raises(ValueError, match="kind must be 'line', 'categorical', or 'image'"):
        sample_db.plot_downhole("geology", "LITHO", kind="scatter")


def test_plot_downhole_multi_hole_grid_returns_axes(sample_db):
    axes = sample_db.plot_downhole("geology", "LITHO", holes=["DH001", "DH002"], layout="grid")
    assert isinstance(axes, np.ndarray)
    assert axes.size >= 2
