"""
Tests for DrillHoleDatabase class.

Tests the clean implementation following AGENTS.md specifications.
"""

import pytest
import pandas as pd
import numpy as np
from loopresources.drillhole.drillhole_database import DrillholeDatabase, DrillHole
from loopresources.drillhole.dhconfig import DhConfig
from loopresources.drillhole.resample import resample_interval_to_new_interval


class TestDrillholeDatabase:
    """Test suite for DrillholeDatabase class."""

    @pytest.fixture
    def sample_collar(self):
        """Create sample collar data."""
        return pd.DataFrame(
            {
                DhConfig.holeid: ["DH001", "DH002", "DH003"],
                DhConfig.x: [100.0, 200.0, 300.0],
                DhConfig.y: [1000.0, 2000.0, 3000.0],
                DhConfig.z: [50.0, 60.0, 70.0],
                DhConfig.total_depth: [100.0, 150.0, 200.0],
            }
        )

    @pytest.fixture
    def sample_survey(self):
        """Create sample survey data."""
        return pd.DataFrame(
            {
                DhConfig.holeid: ["DH001", "DH001", "DH002", "DH002", "DH003"],
                DhConfig.depth: [0.0, 50.0, 0.0, 75.0, 0.0],
                DhConfig.azimuth: [0.0, 0.0, 45.0, 45.0, 90.0],
                DhConfig.dip: [90.0, 90.0, 80.0, 80.0, 85.0],
            }
        )

    @pytest.fixture
    def sample_geology(self):
        """Create sample geology interval data."""
        return pd.DataFrame(
            {
                DhConfig.holeid: ["DH001", "DH001", "DH002", "DH003"],
                DhConfig.sample_from: [0.0, 30.0, 0.0, 0.0],
                DhConfig.sample_to: [30.0, 80.0, 100.0, 150.0],
                "LITHO": ["granite", "schist", "granite", "sandstone"],
            }
        )

    @pytest.fixture
    def irregular_lithology(self):
        """Create irregular lithology data for resampling tests."""
        return pd.DataFrame(
            {
                DhConfig.holeid: ["DH001", "DH001", "DH001", "DH001"],
                DhConfig.sample_from: [0.0, 10.0, 25.0, 50.0],
                DhConfig.sample_to: [10.0, 25.0, 50.0, 100.0],
                "LITHO": ["Granite", "Schist", "Granite", "Sandstone"],
            }
        )

    def test_basic_functionality(self, sample_collar, sample_survey, sample_geology):
        """Test basic database functionality."""
        db = DrillholeDatabase(sample_collar, sample_survey)

        assert len(db.collar) == 3
        assert len(db.survey) == 5
        assert len(db.intervals) == 0
        assert len(db.points) == 0

        # Test adding interval table
        db.add_interval_table("geology", sample_geology)
        assert "geology" in db.intervals
        assert len(db.intervals["geology"]) == 4

        # Test list holes
        holes = db.list_holes()
        assert holes == ["DH001", "DH002", "DH003"]

        # Test extent
        # bb = db.extent()
        # xmin = bb.global_origin[0]
        # xmax = bb.global_maximum[0]
        # assert xmin > 100.0
        # assert xmax < 320.0
        ##todo calculate actual expected extent values and assert here

    def test_iteration(self, sample_collar, sample_survey):
        """Test iteration over drillholes in database."""
        db = DrillholeDatabase(sample_collar, sample_survey)

        # Test iteration returns DrillHole objects
        hole_ids = []
        for drillhole in db:
            assert isinstance(drillhole, DrillHole)
            hole_ids.append(drillhole.hole_id)

        # Check all holes were iterated
        assert hole_ids == ["DH001", "DH002", "DH003"]

        # Test iteration twice to ensure it's reusable
        hole_ids_second = [h.hole_id for h in db]
        assert hole_ids_second == ["DH001", "DH002", "DH003"]

    def test_sorted_by_collar_column(self, sample_collar, sample_survey):
        """Test sorting by collar column."""
        db = DrillholeDatabase(sample_collar, sample_survey)

        # Sort by EAST coordinate (ascending)
        hole_ids = [h.hole_id for h in db.sorted_by("EAST")]
        assert hole_ids == ["DH001", "DH002", "DH003"]

        # Sort by EAST coordinate (descending)
        hole_ids = [h.hole_id for h in db.sorted_by("EAST", reverse=True)]
        assert hole_ids == ["DH003", "DH002", "DH001"]

        # Sort by DEPTH (descending) - should be ['DH003', 'DH002', 'DH001']
        hole_ids = [h.hole_id for h in db.sorted_by("DEPTH", reverse=True)]
        assert hole_ids == ["DH003", "DH002", "DH001"]

    def test_sorted_by_custom_function(self, sample_collar, sample_survey):
        """Test sorting by custom function."""
        db = DrillholeDatabase(sample_collar, sample_survey)

        # Add assay data
        assay = pd.DataFrame(
            {
                DhConfig.holeid: ["DH001", "DH001", "DH002", "DH002", "DH003"],
                DhConfig.depth: [10.0, 50.0, 20.0, 80.0, 30.0],
                "CU_PPM": [500.0, 800.0, 1200.0, 300.0, 600.0],
            }
        )
        db.add_point_table("assay", assay)

        # Sort by maximum Cu value (descending)
        def max_cu(hole):
            try:
                assay_data = hole["assay"]
                return assay_data["CU_PPM"].max() if not assay_data.empty else 0
            except KeyError:
                return 0

        hole_ids = [h.hole_id for h in db.sorted_by(max_cu, reverse=True)]
        assert hole_ids == [
            "DH002",
            "DH001",
            "DH003",
        ]  # DH002 has 1200, DH001 has 800, DH003 has 600

    def test_sorted_by_meters_above_threshold(self, sample_collar, sample_survey):
        """Test sorting by computed metric (meters where value > threshold)."""
        db = DrillholeDatabase(sample_collar, sample_survey)

        # Add geology interval data with grades
        geology = pd.DataFrame(
            {
                DhConfig.holeid: ["DH001", "DH001", "DH002", "DH003", "DH003"],
                DhConfig.sample_from: [0.0, 30.0, 0.0, 0.0, 50.0],
                DhConfig.sample_to: [30.0, 80.0, 100.0, 50.0, 150.0],
                "GRADE": [0.5, 1.5, 2.0, 0.3, 1.8],
            }
        )
        db.add_interval_table("geology", geology)

        # Function to calculate meters with grade > 1.0
        def high_grade_meters(hole):
            try:
                geol = hole["geology"]
                if geol.empty:
                    return 0
                high_grade = geol[geol["GRADE"] > 1.0]
                return (high_grade[DhConfig.sample_to] - high_grade[DhConfig.sample_from]).sum()
            except KeyError:
                return 0

        hole_ids = [h.hole_id for h in db.sorted_by(high_grade_meters, reverse=True)]
        # DH002: 100m at 2.0 = 100m
        # DH003: 100m at 1.8 = 100m
        # DH001: 50m at 1.5 = 50m
        # Order should be DH002 or DH003 (both 100m), then DH001 (50m)
        assert hole_ids[2] == "DH001"  # DH001 should be last (50m)
        assert hole_ids[0] in ["DH002", "DH003"]  # Both have 100m

    def test_sorted_by_none_default(self, sample_collar, sample_survey):
        """Test default sorting by hole_id."""
        db = DrillholeDatabase(sample_collar, sample_survey)

        # Default sort should be by hole_id
        hole_ids = [h.hole_id for h in db.sorted_by()]
        assert hole_ids == ["DH001", "DH002", "DH003"]

        # Same as sorted_by(None)
        hole_ids = [h.hole_id for h in db.sorted_by(None)]
        assert hole_ids == ["DH001", "DH002", "DH003"]


class TestIntervalResampling:
    """Test suite for interval resampling functionality."""

    @pytest.fixture
    def sample_collar(self):
        """Create sample collar data."""
        return pd.DataFrame(
            {
                DhConfig.holeid: ["DH001"],
                DhConfig.x: [100.0],
                DhConfig.y: [1000.0],
                DhConfig.z: [50.0],
                DhConfig.total_depth: [100.0],
            }
        )

    @pytest.fixture
    def sample_survey(self):
        """Create sample survey data."""
        return pd.DataFrame(
            {
                DhConfig.holeid: ["DH001", "DH001"],
                DhConfig.depth: [0.0, 50.0],
                DhConfig.azimuth: [0.0, 0.0],
                DhConfig.dip: [90.0, 90.0],
            }
        )

    @pytest.fixture
    def irregular_lithology(self):
        """Create irregular lithology data for resampling tests."""
        return pd.DataFrame(
            {
                DhConfig.holeid: ["DH001", "DH001", "DH001", "DH001"],
                DhConfig.sample_from: [0.0, 10.0, 25.0, 50.0],
                DhConfig.sample_to: [10.0, 25.0, 50.0, 100.0],
                "LITHO": ["Granite", "Schist", "Granite", "Sandstone"],
            }
        )

    def test_resample_interval_to_new_interval_basic(self, irregular_lithology):
        """Test basic interval resampling."""
        resampled = resample_interval_to_new_interval(
            irregular_lithology, ["LITHO"], new_interval=1.0
        )
        # Should have 100 intervals (0-100m at 1m spacing)
        assert len(resampled) == 100

        # Check first interval is Granite (0-10m range)
        assert resampled.iloc[0]["LITHO"] == "Granite"

        # Check interval at 15m is Schist (10-25m range)
        assert resampled.iloc[15]["LITHO"] == "Schist"

        # Check interval at 30m is Granite (25-50m range)
        assert resampled.iloc[30]["LITHO"] == "Granite"

        # Check interval at 60m is Sandstone (50-100m range)
        assert resampled.iloc[60]["LITHO"] == "Sandstone"

    def test_resample_interval_to_new_interval_5m(self, irregular_lithology):
        """Test interval resampling with 5m intervals."""
        resampled = resample_interval_to_new_interval(
            irregular_lithology, ["LITHO"], new_interval=5.0
        )

        # Should have 20 intervals (0-100m at 5m spacing)
        assert len(resampled) == 20

        # Check 0-5m is Granite
        assert resampled.iloc[0]["LITHO"] == "Granite"

        # Check 10-15m is Schist
        assert resampled.iloc[2]["LITHO"] == "Schist"

        # Check 50-55m is Sandstone
        assert resampled.iloc[10]["LITHO"] == "Sandstone"

    def test_resample_interval_mode_selection(self):
        """Test that mode selection picks the value with biggest occurrence."""
        # Create data where one interval spans multiple lithologies
        data = pd.DataFrame(
            {
                DhConfig.holeid: ["DH001", "DH001", "DH001"],
                DhConfig.sample_from: [0.0, 2.0, 7.0],
                DhConfig.sample_to: [2.0, 7.0, 10.0],
                "LITHO": ["A", "B", "C"],
            }
        )

        resampled = resample_interval_to_new_interval(data, ["LITHO"], new_interval=5.0)
        # First 5m interval (0-5m) should be 'B' (has 3m vs 2m for 'A')
        assert resampled.iloc[0]["LITHO"] == "B"

        # Second 5m interval (5-10m) should be 'B' (2m) or 'C' (3m) - should be 'C'
        assert resampled.iloc[1]["LITHO"] == "C"

    def test_drillhole_resample_method(self, sample_collar, sample_survey, irregular_lithology):
        """Test the DrillHole.resample() method."""
        db = DrillholeDatabase(sample_collar, sample_survey)
        db.add_interval_table("lithology", irregular_lithology)

        hole = db["DH001"]
        resampled = hole.resample("lithology", ["LITHO"], new_interval=1.0)

        # Should have 100 intervals
        assert len(resampled) == 100

        # Check some key values
        assert resampled.iloc[0]["LITHO"] == "Granite"
        assert resampled.iloc[15]["LITHO"] == "Schist"
        assert resampled.iloc[60]["LITHO"] == "Sandstone"

    def test_empty_table_handling(self):
        """Test that empty tables are handled gracefully."""
        empty_df = pd.DataFrame(columns=[DhConfig.sample_from, DhConfig.sample_to, "LITHO"])

        resampled = resample_interval_to_new_interval(empty_df, ["LITHO"], new_interval=1.0)

        # Should return empty DataFrame
        assert len(resampled) == 0

    def test_vtk_with_missing_hole_data(self):
        """Test VTK creation when some holes have no interval data."""
        # Create collar and survey for 3 holes
        collar = pd.DataFrame(
            {
                DhConfig.holeid: ["DH001", "DH002", "DH003"],
                DhConfig.x: [100.0, 200.0, 300.0],
                DhConfig.y: [1000.0, 2000.0, 3000.0],
                DhConfig.z: [50.0, 60.0, 70.0],
                DhConfig.total_depth: [100.0, 150.0, 80.0],
            }
        )

        survey = pd.DataFrame(
            {
                DhConfig.holeid: ["DH001", "DH001", "DH002", "DH002", "DH003", "DH003"],
                DhConfig.depth: [0.0, 50.0, 0.0, 75.0, 0.0, 40.0],
                DhConfig.azimuth: [0.0, 0.0, 45.0, 45.0, 90.0, 90.0],
                DhConfig.dip: [90.0, 90.0, 80.0, 80.0, 85.0, 85.0],
            }
        )

        # Create lithology data for only DH001, not DH002 or DH003
        partial_lithology = pd.DataFrame(
            {
                DhConfig.holeid: ["DH001", "DH001"],
                DhConfig.sample_from: [0.0, 50.0],
                DhConfig.sample_to: [50.0, 100.0],
                "LITHO": ["Granite", "Sandstone"],
            }
        )

        db = DrillholeDatabase(collar, survey)
        db.add_interval_table("lithology", partial_lithology)

        try:
            import pyvista as pv  # noqa: F401

        except ImportError:
            pytest.skip("PyVista not installed")

        # Test single hole without data - should get NaN values
        hole_no_data = db["DH002"]
        tube = hole_no_data.vtk(newinterval=5.0, properties=["lithology"])

        # Should have lithology data (as NaN)
        assert "LITHO" in tube.cell_data
        litho_values = tube.cell_data["LITHO"]
        assert np.all(pd.isna(litho_values))

        # Test database-level VTK with mixed data
        multiblock = db.vtk(newinterval=5.0, properties=["lithology"])

        # All holes should be in multiblock
        assert len(multiblock) == 3

        # Check DH001 has real data
        assert "LITHO" in multiblock["DH001"].cell_data
        dh001_litho = multiblock["DH001"].cell_data["LITHO"]
        assert not np.all(pd.isna(dh001_litho))  # Should have real values

        # Check DH002 and DH003 have NaN data
        for hole_id in ["DH002", "DH003"]:
            assert "LITHO" in multiblock[hole_id].cell_data
            hole_litho = multiblock[hole_id].cell_data["LITHO"]
            assert np.all(pd.isna(hole_litho))  # Should be all NaN


if __name__ == "__main__":
    pytest.main([__file__])
