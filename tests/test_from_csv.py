"""
Tests for DrillholeDatabase.from_csv() method.
"""

import pytest
import pandas as pd
import tempfile
import os
from loopresources.drillhole.drillhole_database import DrillholeDatabase
from loopresources.drillhole.dhconfig import DhConfig


class TestFromCsv:
    """Test suite for DrillholeDatabase.from_csv() class method."""

    @pytest.fixture
    def sample_collar_data(self):
        """Sample collar data with custom column names."""
        return {
            "HOLE_ID": ["DH001", "DH002", "DH003"],
            "X_MGA": [100.0, 200.0, 300.0],
            "Y_MGA": [1000.0, 2000.0, 3000.0],
            "Z_MGA": [50.0, 60.0, 70.0],
            "DEPTH": [100.0, 150.0, 200.0],
        }

    @pytest.fixture
    def sample_survey_data(self):
        """Sample survey data with custom column names."""
        return {
            "Drillhole ID": ["DH001", "DH001", "DH002", "DH002", "DH003"],
            "Depth": [0.0, 50.0, 0.0, 75.0, 0.0],
            "Azimuth": [0.0, 0.0, 45.0, 45.0, 90.0],
            "Dip": [90.0, 90.0, 80.0, 80.0, 85.0],
        }

    def test_from_csv_with_mapping(self, sample_collar_data, sample_survey_data):
        """Test from_csv with column mapping."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create CSV files
            collar_file = os.path.join(tmpdir, "collar.csv")
            survey_file = os.path.join(tmpdir, "survey.csv")
            pd.DataFrame(sample_collar_data).to_csv(collar_file, index=False)
            pd.DataFrame(sample_survey_data).to_csv(survey_file, index=False)

            # Load with column mapping
            db = DrillholeDatabase.from_csv(
                collar_file=collar_file,
                survey_file=survey_file,
                collar_columns={
                    "HOLE_ID": DhConfig.holeid,
                    "X_MGA": DhConfig.x,
                    "Y_MGA": DhConfig.y,
                    "Z_MGA": DhConfig.z,
                    "DEPTH": DhConfig.total_depth,
                },
                survey_columns={
                    "Drillhole ID": DhConfig.holeid,
                    "Depth": DhConfig.depth,
                    "Azimuth": DhConfig.azimuth,
                    "Dip": DhConfig.dip,
                },
            )

            # Verify the data was loaded correctly
            assert len(db.list_holes()) == 3
            assert "DH001" in db.list_holes()
            assert len(db.collar) == 3
            assert len(db.survey) == 5

            # Check that columns were mapped correctly
            assert DhConfig.holeid in db.collar.columns
            assert DhConfig.x in db.collar.columns
            assert DhConfig.y in db.collar.columns
            assert DhConfig.z in db.collar.columns
            assert DhConfig.total_depth in db.collar.columns

    def test_from_csv_without_mapping(self):
        """Test from_csv without column mapping (columns already match DhConfig)."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create collar CSV with DhConfig column names
            collar_data = {
                DhConfig.holeid: ["DH001", "DH002"],
                DhConfig.x: [100.0, 200.0],
                DhConfig.y: [1000.0, 2000.0],
                DhConfig.z: [50.0, 60.0],
                DhConfig.total_depth: [100.0, 150.0],
            }
            collar_file = os.path.join(tmpdir, "collar.csv")
            pd.DataFrame(collar_data).to_csv(collar_file, index=False)

            # Create survey CSV with DhConfig column names
            survey_data = {
                DhConfig.holeid: ["DH001", "DH001", "DH002"],
                DhConfig.depth: [0.0, 50.0, 0.0],
                DhConfig.azimuth: [0.0, 0.0, 45.0],
                DhConfig.dip: [90.0, 90.0, 80.0],
            }
            survey_file = os.path.join(tmpdir, "survey.csv")
            pd.DataFrame(survey_data).to_csv(survey_file, index=False)

            # Load without mapping
            db = DrillholeDatabase.from_csv(collar_file=collar_file, survey_file=survey_file)

            # Verify the data was loaded correctly
            assert len(db.list_holes()) == 2
            assert "DH001" in db.list_holes()

    def test_from_csv_missing_column_error(self, sample_collar_data, sample_survey_data):
        """Test that from_csv raises error when mapped column doesn't exist."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create CSV files
            collar_file = os.path.join(tmpdir, "collar.csv")
            survey_file = os.path.join(tmpdir, "survey.csv")
            pd.DataFrame(sample_collar_data).to_csv(collar_file, index=False)
            pd.DataFrame(sample_survey_data).to_csv(survey_file, index=False)

            # Try to load with invalid column mapping
            with pytest.raises(KeyError, match="Required collar column 'HOLEID' not found in CSV file"):
                DrillholeDatabase.from_csv(
                    collar_file=collar_file,
                    survey_file=survey_file,
                    collar_columns={
                        "INVALID_COLUMN": DhConfig.holeid,
                        "X_MGA": DhConfig.x,
                        "Y_MGA": DhConfig.y,
                        "Z_MGA": DhConfig.z,
                        "DEPTH": DhConfig.total_depth,
                    },
                )

    def test_from_csv_with_missing_values(self):
        """Test that from_csv drops rows with missing essential data."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create collar CSV with some missing values
            collar_data = {
                DhConfig.holeid: ["DH001", "DH002", "DH003"],
                DhConfig.x: [100.0, 200.0, None],  # Missing X for DH003
                DhConfig.y: [1000.0, 2000.0, 3000.0],
                DhConfig.z: [50.0, 60.0, 70.0],
                DhConfig.total_depth: [100.0, 150.0, 200.0],
            }
            collar_file = os.path.join(tmpdir, "collar.csv")
            pd.DataFrame(collar_data).to_csv(collar_file, index=False)

            # Create survey CSV
            survey_data = {
                DhConfig.holeid: ["DH001", "DH002"],
                DhConfig.depth: [0.0, 0.0],
                DhConfig.azimuth: [0.0, 45.0],
                DhConfig.dip: [90.0, 80.0],
            }
            survey_file = os.path.join(tmpdir, "survey.csv")
            pd.DataFrame(survey_data).to_csv(survey_file, index=False)

            # Load data
            db = DrillholeDatabase.from_csv(collar_file=collar_file, survey_file=survey_file)

            # Verify that DH003 was dropped due to missing X
            assert len(db.list_holes()) == 2
            assert "DH003" not in db.list_holes()

    def test_from_csv_preserves_extra_columns(self, sample_collar_data, sample_survey_data):
        """Test that from_csv preserves extra columns not in the mapping."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Add extra columns to the data
            collar_data = sample_collar_data.copy()
            collar_data["EXTRA_INFO"] = ["info1", "info2", "info3"]

            collar_file = os.path.join(tmpdir, "collar.csv")
            survey_file = os.path.join(tmpdir, "survey.csv")
            pd.DataFrame(collar_data).to_csv(collar_file, index=False)
            pd.DataFrame(sample_survey_data).to_csv(survey_file, index=False)

            # Load with partial column mapping
            db = DrillholeDatabase.from_csv(
                collar_file=collar_file,
                survey_file=survey_file,
                collar_columns={
                    "HOLE_ID": DhConfig.holeid,
                    "X_MGA": DhConfig.x,
                    "Y_MGA": DhConfig.y,
                    "Z_MGA": DhConfig.z,
                    "DEPTH": DhConfig.total_depth,
                },
                survey_columns={
                    "Drillhole ID": DhConfig.holeid,
                    "Depth": DhConfig.depth,
                    "Azimuth": DhConfig.azimuth,
                    "Dip": DhConfig.dip,
                },
            )

            # Verify extra column is preserved
            assert "EXTRA_INFO" in db.collar.columns


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
