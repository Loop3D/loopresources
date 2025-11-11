"""
Tests for optimized database queries.

Tests that verify the optimized query methods that fetch data for specific holes
without loading entire tables into memory.
"""

import pytest
import pandas as pd
import tempfile
import os
import sqlite3

from loopresources.drillhole.drillhole_database import DrillholeDatabase
from loopresources.drillhole.dbconfig import DbConfig
from loopresources.drillhole.dhconfig import DhConfig


class TestOptimizedQueries:
    """Test suite for optimized database query methods."""

    @pytest.fixture
    def sample_collar(self):
        """Create sample collar data with multiple holes."""
        return pd.DataFrame(
            {
                DhConfig.holeid: ["DH001", "DH002", "DH003", "DH004", "DH005"],
                DhConfig.x: [100.0, 200.0, 300.0, 400.0, 500.0],
                DhConfig.y: [1000.0, 2000.0, 3000.0, 4000.0, 5000.0],
                DhConfig.z: [50.0, 60.0, 70.0, 80.0, 90.0],
                DhConfig.total_depth: [100.0, 150.0, 200.0, 250.0, 300.0],
            }
        )

    @pytest.fixture
    def sample_survey(self):
        """Create sample survey data with multiple holes."""
        return pd.DataFrame(
            {
                DhConfig.holeid: [
                    "DH001",
                    "DH001",
                    "DH002",
                    "DH002",
                    "DH003",
                    "DH003",
                    "DH004",
                    "DH005",
                ],
                DhConfig.depth: [0.0, 50.0, 0.0, 75.0, 0.0, 100.0, 0.0, 0.0],
                DhConfig.azimuth: [0.0, 0.0, 45.0, 45.0, 90.0, 90.0, 135.0, 180.0],
                DhConfig.dip: [90.0, 90.0, 80.0, 80.0, 85.0, 85.0, 75.0, 70.0],
            }
        )

    @pytest.fixture
    def temp_db_path(self):
        """Create a temporary database path."""
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
            db_path = f.name
        yield db_path
        # Cleanup
        if os.path.exists(db_path):
            os.unlink(db_path)

    def test_get_collar_for_hole_memory(self, sample_collar, sample_survey):
        """Test get_collar_for_hole with memory backend."""
        db = DrillholeDatabase(sample_collar, sample_survey)

        # Get collar for specific hole
        collar_dh001 = db.get_collar_for_hole("DH001")

        assert len(collar_dh001) == 1
        assert collar_dh001[DhConfig.holeid].iloc[0] == "DH001"
        assert collar_dh001[DhConfig.x].iloc[0] == 100.0

    def test_get_survey_for_hole_memory(self, sample_collar, sample_survey):
        """Test get_survey_for_hole with memory backend."""
        db = DrillholeDatabase(sample_collar, sample_survey)

        # Get survey for specific hole
        survey_dh001 = db.get_survey_for_hole("DH001")

        assert len(survey_dh001) == 2
        assert all(survey_dh001[DhConfig.holeid] == "DH001")

    def test_get_collar_for_hole_file(self, sample_collar, sample_survey, temp_db_path):
        """Test get_collar_for_hole with file backend."""
        db_config = DbConfig(backend="file", db_path=temp_db_path, project_name="test")
        db = DrillholeDatabase(sample_collar, sample_survey, db_config)

        # Get collar for specific hole
        collar_dh002 = db.get_collar_for_hole("DH002")

        assert len(collar_dh002) == 1
        assert collar_dh002[DhConfig.holeid].iloc[0] == "DH002"
        assert collar_dh002[DhConfig.x].iloc[0] == 200.0

    def test_get_survey_for_hole_file(self, sample_collar, sample_survey, temp_db_path):
        """Test get_survey_for_hole with file backend."""
        db_config = DbConfig(backend="file", db_path=temp_db_path, project_name="test")
        db = DrillholeDatabase(sample_collar, sample_survey, db_config)

        # Get survey for specific hole
        survey_dh002 = db.get_survey_for_hole("DH002")

        assert len(survey_dh002) == 2
        assert all(survey_dh002[DhConfig.holeid] == "DH002")

    def test_drillhole_uses_optimized_methods_file(
        self, sample_collar, sample_survey, temp_db_path
    ):
        """Test that DrillHole uses optimized methods with file backend."""
        db_config = DbConfig(backend="file", db_path=temp_db_path, project_name="test")
        db = DrillholeDatabase(sample_collar, sample_survey, db_config)

        # Create DrillHole instance - should use optimized queries
        drillhole = db["DH003"]

        assert len(drillhole.collar) == 1
        assert drillhole.collar[DhConfig.holeid].iloc[0] == "DH003"
        assert len(drillhole.survey) == 2
        assert all(drillhole.survey[DhConfig.holeid] == "DH003")

    def test_query_only_fetches_specific_hole(self, sample_collar, sample_survey, temp_db_path):
        """Test that database query only fetches data for specific hole."""
        db_config = DbConfig(backend="file", db_path=temp_db_path, project_name="test")
        db = DrillholeDatabase(sample_collar, sample_survey, db_config)

        # Verify database contains all holes
        conn = sqlite3.connect(temp_db_path)
        cursor = conn.cursor()
        cursor.execute(
            "SELECT COUNT(DISTINCT HOLEID) FROM collar WHERE project_id = (SELECT id FROM projects WHERE name = 'test')"
        )
        total_holes = cursor.fetchone()[0]
        assert total_holes == 5

        # Get data for single hole using optimized method
        collar_dh004 = db.get_collar_for_hole("DH004")

        # Verify we only got data for one hole
        assert len(collar_dh004) == 1
        assert collar_dh004[DhConfig.holeid].iloc[0] == "DH004"

        conn.close()

    def test_get_interval_data_for_hole(self, sample_collar, sample_survey):
        """Test get_interval_data_for_hole method."""
        db = DrillholeDatabase(sample_collar, sample_survey)

        # Add interval table
        geology = pd.DataFrame(
            {
                DhConfig.holeid: ["DH001", "DH001", "DH002", "DH003"],
                DhConfig.sample_from: [0.0, 30.0, 0.0, 0.0],
                DhConfig.sample_to: [30.0, 80.0, 100.0, 150.0],
                "LITHO": ["granite", "schist", "granite", "sandstone"],
            }
        )
        db.add_interval_table("geology", geology)

        # Get interval data for specific hole
        geology_dh001 = db.get_interval_data_for_hole("geology", "DH001")

        assert len(geology_dh001) == 2
        assert all(geology_dh001[DhConfig.holeid] == "DH001")
        assert list(geology_dh001["LITHO"]) == ["granite", "schist"]

    def test_get_point_data_for_hole(self, sample_collar, sample_survey):
        """Test get_point_data_for_hole method."""
        db = DrillholeDatabase(sample_collar, sample_survey)

        # Add point table
        assay = pd.DataFrame(
            {
                DhConfig.holeid: ["DH001", "DH002", "DH003"],
                DhConfig.depth: [10.0, 50.0, 75.0],
                "CU_PPM": [500.0, 800.0, 650.0],
            }
        )
        db.add_point_table("assay", assay)

        # Get point data for specific hole
        assay_dh002 = db.get_point_data_for_hole("assay", "DH002")

        assert len(assay_dh002) == 1
        assert assay_dh002[DhConfig.holeid].iloc[0] == "DH002"
        assert assay_dh002["CU_PPM"].iloc[0] == 800.0

    def test_drillhole_getitem_uses_optimized_methods(self, sample_collar, sample_survey):
        """Test that DrillHole.__getitem__ uses optimized methods."""
        db = DrillholeDatabase(sample_collar, sample_survey)

        # Add interval and point tables
        geology = pd.DataFrame(
            {
                DhConfig.holeid: ["DH001", "DH001", "DH002"],
                DhConfig.sample_from: [0.0, 30.0, 0.0],
                DhConfig.sample_to: [30.0, 80.0, 100.0],
                "LITHO": ["granite", "schist", "granite"],
            }
        )
        db.add_interval_table("geology", geology)

        assay = pd.DataFrame(
            {
                DhConfig.holeid: ["DH001", "DH002"],
                DhConfig.depth: [10.0, 50.0],
                "CU_PPM": [500.0, 800.0],
            }
        )
        db.add_point_table("assay", assay)

        # Access via DrillHole
        drillhole = db["DH001"]

        # Get interval table
        geology_dh001 = drillhole["geology"]
        assert len(geology_dh001) == 2
        assert all(geology_dh001[DhConfig.holeid] == "DH001")

        # Get point table
        assay_dh001 = drillhole["assay"]
        assert len(assay_dh001) == 1
        assert assay_dh001[DhConfig.holeid].iloc[0] == "DH001"
