"""
Tests for __str__ and __repr__ methods.

Tests the string representations of DrillHole, DrillholeDatabase, and DhConfig classes.
"""

import pytest
import pandas as pd
import numpy as np
from loopresources.drillhole.drillhole_database import DrillholeDatabase
from loopresources.drillhole.dhconfig import DhConfig


class TestDhConfigStringRepresentations:
    """Test suite for DhConfig string representations."""

    def test_dhconfig_repr(self):
        """Test DhConfig __repr__ method."""
        # Since DhConfig is a class with class attributes, repr will show class info
        repr_str = repr(DhConfig)
        assert "DhConfig" in repr_str

    def test_dhconfig_str(self):
        """Test DhConfig __str__ method."""
        # Since DhConfig is a class with class attributes, str will show class info
        str_str = str(DhConfig)
        assert "DhConfig" in str_str


class TestDrillholeDatabaseStringRepresentations:
    """Test suite for DrillholeDatabase string representations."""

    @pytest.fixture
    def sample_database(self):
        """Create sample database with data."""
        collar = pd.DataFrame(
            {
                DhConfig.holeid: ["DH001", "DH002", "DH003"],
                DhConfig.x: [100.0, 200.0, 300.0],
                DhConfig.y: [1000.0, 2000.0, 3000.0],
                DhConfig.z: [50.0, 60.0, 70.0],
                DhConfig.total_depth: [150.0, 200.0, 180.0],
            }
        )

        survey = pd.DataFrame(
            {
                DhConfig.holeid: ["DH001", "DH001", "DH002", "DH002", "DH003"],
                DhConfig.depth: [0.0, 50.0, 0.0, 100.0, 0.0],
                DhConfig.azimuth: [0.0, 5.0, 45.0, 50.0, 90.0],
                DhConfig.dip: [90.0, 88.0, 80.0, 78.0, 85.0],
            }
        )

        geology = pd.DataFrame(
            {
                DhConfig.holeid: ["DH001", "DH001", "DH002", "DH003"],
                DhConfig.sample_from: [0.0, 40.0, 0.0, 0.0],
                DhConfig.sample_to: [40.0, 80.0, 100.0, 150.0],
                "LITHO": ["granite", "schist", "sandstone", "limestone"],
            }
        )

        assay = pd.DataFrame(
            {
                DhConfig.holeid: ["DH001", "DH001", "DH002"],
                DhConfig.sample_from: [10.0, 50.0, 20.0],
                DhConfig.sample_to: [30.0, 70.0, 40.0],
                "CU_PPM": [500.0, 1200.0, 800.0],
                "AU_PPM": [0.5, 1.2, 0.8],
            }
        )

        db = DrillholeDatabase(collar, survey)
        db.add_interval_table("geology", geology)
        db.add_interval_table("assay", assay)

        return db

    @pytest.fixture
    def empty_database(self):
        """Create empty database with minimal data."""
        collar = pd.DataFrame(
            {
                DhConfig.holeid: ["DH001"],
                DhConfig.x: [100.0],
                DhConfig.y: [1000.0],
                DhConfig.z: [50.0],
                DhConfig.total_depth: [100.0],
            }
        )

        survey = pd.DataFrame(
            {
                DhConfig.holeid: ["DH001"],
                DhConfig.depth: [0.0],
                DhConfig.azimuth: [0.0],
                DhConfig.dip: [90.0],
            }
        )

        return DrillholeDatabase(collar, survey)

    def test_database_repr(self, sample_database):
        """Test DrillholeDatabase __repr__ method."""
        repr_str = repr(sample_database)

        # Check that key information is present
        assert "DrillholeDatabase" in repr_str
        assert "holes=3" in repr_str
        assert "interval_tables=2" in repr_str
        assert "point_tables=0" in repr_str

    def test_database_str(self, sample_database):
        """Test DrillholeDatabase __str__ method."""
        str_str = str(sample_database)

        # Check that key sections are present
        assert "DrillholeDatabase" in str_str
        assert "Number of Drillholes: 3" in str_str
        assert "Spatial Extent:" in str_str
        assert "Interval Tables (2):" in str_str

        # Check table information
        assert "geology:" in str_str
        assert "assay:" in str_str
        assert "LITHO" in str_str
        assert "CU_PPM" in str_str
        assert "AU_PPM" in str_str

    def test_database_str_with_no_tables(self, empty_database):
        """Test DrillholeDatabase __str__ with no interval/point tables."""
        str_str = str(empty_database)

        assert "DrillholeDatabase" in str_str
        assert "Number of Drillholes: 1" in str_str
        assert "Interval Tables: None" in str_str
        assert "Point Tables: None" in str_str

    def test_database_repr_is_concise(self, sample_database):
        """Test that __repr__ is concise and suitable for debugging."""
        repr_str = repr(sample_database)

        # __repr__ should be relatively short (single line)
        assert len(repr_str.split("\n")) == 1

        # Should contain essential info
        assert "DrillholeDatabase" in repr_str
        assert "holes=" in repr_str

    def test_database_str_is_detailed(self, sample_database):
        """Test that __str__ is detailed and human-readable."""
        str_str = str(sample_database)

        # __str__ should be multi-line and detailed
        lines = str_str.split("\n")
        assert len(lines) > 5

        # Should contain detailed information
        assert any("Spatial Extent" in line for line in lines)
        assert any("Interval Tables" in line for line in lines)


class TestDrillHoleStringRepresentations:
    """Test suite for DrillHole string representations."""

    @pytest.fixture
    def sample_hole(self):
        """Create a sample DrillHole."""
        collar = pd.DataFrame(
            {
                DhConfig.holeid: ["DH001", "DH002"],
                DhConfig.x: [100.0, 200.0],
                DhConfig.y: [1000.0, 2000.0],
                DhConfig.z: [50.0, 60.0],
                DhConfig.total_depth: [150.0, 200.0],
            }
        )

        survey = pd.DataFrame(
            {
                DhConfig.holeid: ["DH001", "DH001", "DH002"],
                DhConfig.depth: [0.0, 50.0, 0.0],
                DhConfig.azimuth: [0.0, 5.0, 45.0],
                DhConfig.dip: [90.0, 88.0, 80.0],
            }
        )

        geology = pd.DataFrame(
            {
                DhConfig.holeid: ["DH001", "DH001"],
                DhConfig.sample_from: [0.0, 40.0],
                DhConfig.sample_to: [40.0, 80.0],
                "LITHO": ["granite", "schist"],
            }
        )

        assay = pd.DataFrame(
            {
                DhConfig.holeid: ["DH001", "DH001"],
                DhConfig.sample_from: [10.0, 50.0],
                DhConfig.sample_to: [30.0, 70.0],
                "CU_PPM": [500.0, 1200.0],
                "AU_PPM": [0.5, 1.2],
            }
        )

        db = DrillholeDatabase(collar, survey)
        db.add_interval_table("geology", geology)
        db.add_interval_table("assay", assay)

        return db["DH001"]

    @pytest.fixture
    def hole_with_no_data(self):
        """Create a DrillHole with no interval/point tables."""
        collar = pd.DataFrame(
            {
                DhConfig.holeid: ["DH001"],
                DhConfig.x: [100.0],
                DhConfig.y: [1000.0],
                DhConfig.z: [50.0],
                DhConfig.total_depth: [100.0],
            }
        )

        survey = pd.DataFrame(
            {
                DhConfig.holeid: ["DH001"],
                DhConfig.depth: [0.0],
                DhConfig.azimuth: [0.0],
                DhConfig.dip: [90.0],
            }
        )

        db = DrillholeDatabase(collar, survey)
        return db["DH001"]

    def test_drillhole_repr(self, sample_hole):
        """Test DrillHole __repr__ method."""
        repr_str = repr(sample_hole)

        # Check that key information is present
        assert "DrillHole" in repr_str
        assert "hole_id" in repr_str or "DH001" in repr_str
        assert "depth=" in repr_str or "150" in repr_str

    def test_drillhole_str(self, sample_hole):
        """Test DrillHole __str__ method."""
        str_str = str(sample_hole)

        # Check that key sections are present
        assert "DrillHole: DH001" in str_str
        assert "Location:" in str_str
        assert "X=100.00" in str_str
        assert "Y=1000.00" in str_str
        assert "Z=50.00" in str_str
        assert "Total Depth: 150.00m" in str_str
        assert "Average Azimuth:" in str_str
        assert "Average Dip:" in str_str

        # Check table information
        assert "Interval Tables" in str_str
        assert "geology" in str_str
        assert "assay" in str_str

    def test_drillhole_str_angles_in_degrees(self, sample_hole):
        """Test that angles are displayed in degrees."""
        str_str = str(sample_hole)

        # The angles should be displayed in degrees (not radians)
        # Average azimuth should be around 2.5 degrees
        # Average dip should be around 89 degrees
        lines = str_str.split("\n")

        azimuth_line = [line for line in lines if "Average Azimuth:" in line][0]
        dip_line = [line for line in lines if "Average Dip:" in line][0]

        # Extract numeric values
        assert "°" in azimuth_line
        assert "°" in dip_line

        # Values should be reasonable for degrees (not radians which would be < 2)
        # Average azimuth ~2.5 degrees
        assert "2.5" in azimuth_line or "2.50" in azimuth_line
        # Average dip ~89 degrees
        assert "89" in dip_line

    def test_drillhole_str_with_no_tables(self, hole_with_no_data):
        """Test DrillHole __str__ with no interval/point tables."""
        str_str = str(hole_with_no_data)

        assert "DrillHole: DH001" in str_str
        assert "Interval Tables: None" in str_str
        assert "Point Tables: None" in str_str

    def test_drillhole_str_statistics(self, sample_hole):
        """Test that statistics are shown for numerical columns."""
        str_str = str(sample_hole)

        # Check statistics for numerical columns
        assert "CU_PPM:" in str_str
        assert "mean=" in str_str
        assert "min=" in str_str
        assert "max=" in str_str

        # Check categorical columns
        assert "LITHO:" in str_str
        assert "unique values" in str_str

    def test_drillhole_repr_is_concise(self, sample_hole):
        """Test that __repr__ is concise."""
        repr_str = repr(sample_hole)

        # __repr__ should be a single line
        assert len(repr_str.split("\n")) == 1

        # Should contain essential info
        assert "DrillHole" in repr_str
        assert "DH001" in repr_str

    def test_drillhole_str_is_detailed(self, sample_hole):
        """Test that __str__ is detailed."""
        str_str = str(sample_hole)

        # __str__ should be multi-line and detailed
        lines = str_str.split("\n")
        assert len(lines) > 10

        # Should contain detailed information
        assert any("Location" in line for line in lines)
        assert any("Interval Tables" in line for line in lines)
        assert any("geology" in line for line in lines)


class TestStringRepresentationEdgeCases:
    """Test edge cases for string representations."""

    def test_database_with_point_tables(self):
        """Test database with point tables."""
        collar = pd.DataFrame(
            {
                DhConfig.holeid: ["DH001"],
                DhConfig.x: [100.0],
                DhConfig.y: [1000.0],
                DhConfig.z: [50.0],
                DhConfig.total_depth: [100.0],
            }
        )

        survey = pd.DataFrame(
            {
                DhConfig.holeid: ["DH001"],
                DhConfig.depth: [0.0],
                DhConfig.azimuth: [0.0],
                DhConfig.dip: [90.0],
            }
        )

        point_data = pd.DataFrame(
            {
                DhConfig.holeid: ["DH001", "DH001"],
                DhConfig.depth: [10.0, 50.0],
                "MEASURE": [1.5, 2.3],
            }
        )

        db = DrillholeDatabase(collar, survey)
        db.add_point_table("measurements", point_data)

        str_str = str(db)
        assert "Point Tables (1):" in str_str
        assert "measurements:" in str_str

    def test_drillhole_with_nan_values(self):
        """Test DrillHole with NaN values in data."""
        collar = pd.DataFrame(
            {
                DhConfig.holeid: ["DH001"],
                DhConfig.x: [100.0],
                DhConfig.y: [1000.0],
                DhConfig.z: [50.0],
                DhConfig.total_depth: [100.0],
            }
        )

        survey = pd.DataFrame(
            {
                DhConfig.holeid: ["DH001"],
                DhConfig.depth: [0.0],
                DhConfig.azimuth: [0.0],
                DhConfig.dip: [90.0],
            }
        )

        assay = pd.DataFrame(
            {
                DhConfig.holeid: ["DH001", "DH001"],
                DhConfig.sample_from: [10.0, 50.0],
                DhConfig.sample_to: [30.0, 70.0],
                "CU_PPM": [500.0, np.nan],
                "AU_PPM": [np.nan, 1.2],
            }
        )

        db = DrillholeDatabase(collar, survey)
        db.add_interval_table("assay", assay)

        hole = db["DH001"]
        str_str = str(hole)

        # Should handle NaN values gracefully
        assert "CU_PPM:" in str_str
        assert "AU_PPM:" in str_str
        # Should show count of non-null values
        assert "(n=1)" in str_str
