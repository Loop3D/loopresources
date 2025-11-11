"""
Tests for preprocessing and imputation tools in DrillholeDatabase.

Tests the validate_numerical_columns and filter_by_nan_threshold methods.
"""

import pytest
import pandas as pd
import numpy as np
from loopresources.drillhole.drillhole_database import DrillholeDatabase
from loopresources.drillhole.dhconfig import DhConfig


class TestPreprocessing:
    """Test suite for preprocessing and imputation methods."""

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
    def assay_with_mixed_data(self):
        """Create assay data with mixed data types and invalid values."""
        return pd.DataFrame(
            {
                DhConfig.holeid: ["DH001", "DH001", "DH002", "DH002", "DH003"],
                DhConfig.depth: [10.0, 40.0, 50.0, 80.0, 100.0],
                "CU_PPM": [500.0, -100.0, 0.0, 1200.0, 800.0],  # Has negative and zero
                "AU_PPM": ["0.5", "1.2", "invalid", 0.8, -0.1],  # Has string and negative
                "AG_PPM": [10.0, 20.0, np.nan, 15.0, 25.0],  # Has NaN
            }
        )

    @pytest.fixture
    def database(self, sample_collar, sample_survey):
        """Create a DrillholeDatabase instance."""
        return DrillholeDatabase(sample_collar, sample_survey)

    def test_validate_numerical_columns_converts_strings(self, database, assay_with_mixed_data):
        """Test that string values are converted to numeric and invalid ones become NaN."""
        database.add_point_table("assay", assay_with_mixed_data)

        # Validate AU_PPM which has a string value
        database.validate_numerical_columns("assay", ["AU_PPM"])

        # Check that the column is now numeric
        assert pd.api.types.is_numeric_dtype(database.points["assay"]["AU_PPM"])

        # Check that 'invalid' was converted to NaN
        au_values = database.points["assay"]["AU_PPM"].values
        assert pd.isna(au_values[2])  # The 'invalid' string should be NaN

    def test_validate_numerical_columns_removes_negative(self, database, assay_with_mixed_data):
        """Test that negative values are replaced with NaN when allow_negative=False."""
        database.add_point_table("assay", assay_with_mixed_data)

        # Validate CU_PPM which has negative and zero values
        database.validate_numerical_columns("assay", ["CU_PPM"], allow_negative=False)

        cu_values = database.points["assay"]["CU_PPM"].values

        # Index 1 had -100.0, should be NaN
        assert pd.isna(cu_values[1])

        # Index 2 had 0.0, should be NaN (since allow_negative=False means <= 0)
        assert pd.isna(cu_values[2])

        # Index 0 had 500.0, should remain
        assert cu_values[0] == 500.0

    def test_validate_numerical_columns_allows_negative(self, database, assay_with_mixed_data):
        """Test that negative values are replaced but zero is kept when allow_negative=True."""
        database.add_point_table("assay", assay_with_mixed_data)

        # Validate AU_PPM which has negative value
        database.validate_numerical_columns("assay", ["AU_PPM"], allow_negative=True)

        au_values = database.points["assay"]["AU_PPM"].values

        # Index 4 had -0.1, should be NaN
        assert not pd.isna(au_values[4])

        # But string conversion to NaN should still work
        assert pd.isna(au_values[2])  # 'invalid' string

    def test_validate_numerical_columns_chainable(self, database, assay_with_mixed_data):
        """Test that validate_numerical_columns returns self for chaining."""
        database.add_point_table("assay", assay_with_mixed_data)

        # Should be chainable
        result = database.validate_numerical_columns(
            "assay", ["CU_PPM"]
        ).validate_numerical_columns("assay", ["AU_PPM"])

        # Should return the same database instance
        assert result is database

    def test_validate_numerical_columns_interval_table(self, database):
        """Test validation works on interval tables."""
        geology = pd.DataFrame(
            {
                DhConfig.holeid: ["DH001", "DH002"],
                DhConfig.sample_from: [0.0, 0.0],
                DhConfig.sample_to: [30.0, 50.0],
                "GRADE": ["5.5", -2.0],  # Mixed string and negative
            }
        )
        database.add_interval_table("geology", geology)

        database.validate_numerical_columns(
            "geology", ["GRADE"], table_type="interval", allow_negative=False
        )

        grade_values = database.intervals["geology"]["GRADE"].values

        # Check conversion happened
        assert pd.api.types.is_numeric_dtype(database.intervals["geology"]["GRADE"])

        # Check negative was replaced
        assert pd.isna(grade_values[1])

    def test_validate_numerical_columns_missing_column_warning(
        self, database, assay_with_mixed_data
    ):
        """Test that missing columns generate warning but don't fail."""
        database.add_point_table("assay", assay_with_mixed_data)

        # Should not raise an error for missing column
        database.validate_numerical_columns("assay", ["CU_PPM", "MISSING_COLUMN"])

        # CU_PPM should still be processed
        assert pd.api.types.is_numeric_dtype(database.points["assay"]["CU_PPM"])

    def test_validate_numerical_columns_invalid_table_type(self, database):
        """Test that invalid table_type raises error."""
        with pytest.raises(ValueError, match="table not found"):
            database.validate_numerical_columns("assay", ["CU_PPM"], table_type="invalid")

    def test_validate_numerical_columns_table_not_found(self, database):
        """Test that missing table raises KeyError."""
        with pytest.raises(KeyError, match="Table 'missing' not found"):
            database.validate_numerical_columns("missing", ["CU_PPM"])

    def test_filter_by_nan_threshold_basic(self, database):
        """Test basic NaN threshold filtering."""
        assay = pd.DataFrame(
            {
                DhConfig.holeid: ["DH001", "DH001", "DH002", "DH002", "DH003"],
                DhConfig.depth: [10.0, 40.0, 50.0, 80.0, 100.0],
                "CU_PPM": [500.0, np.nan, np.nan, 1200.0, 800.0],
                "AU_PPM": [0.5, 1.2, np.nan, 0.8, np.nan],
                "AG_PPM": [10.0, np.nan, np.nan, 15.0, 25.0],
            }
        )
        database.add_point_table("assay", assay)

        # Filter to keep rows with at least 2/3 (66.7%) valid values
        filtered_db = database.filter_by_nan_threshold(
            "assay", ["CU_PPM", "AU_PPM", "AG_PPM"], threshold=0.66
        )

        # Row 0: 3/3 valid (100%) - keep
        # Row 1: 1/3 valid (33%) - remove
        # Row 2: 0/3 valid (0%) - remove
        # Row 3: 3/3 valid (100%) - keep
        # Row 4: 2/3 valid (66.7%) - keep

        assert len(filtered_db.points["assay"]) == 3
        assert set(filtered_db.points["assay"][DhConfig.depth]) == {10.0, 80.0, 100.0}

    def test_filter_by_nan_threshold_strict(self, database):
        """Test strict threshold (all columns must have values)."""
        assay = pd.DataFrame(
            {
                DhConfig.holeid: ["DH001", "DH001", "DH002"],
                DhConfig.depth: [10.0, 40.0, 50.0],
                "CU_PPM": [500.0, np.nan, 800.0],
                "AU_PPM": [0.5, 1.2, 0.8],
            }
        )
        database.add_point_table("assay", assay)

        # Keep only rows with 100% valid values
        filtered_db = database.filter_by_nan_threshold("assay", ["CU_PPM", "AU_PPM"], threshold=1.0)

        # Only rows 0 and 2 should remain
        assert len(filtered_db.points["assay"]) == 2
        assert 40.0 not in filtered_db.points["assay"][DhConfig.depth].values

    def test_filter_by_nan_threshold_permissive(self, database):
        """Test permissive threshold (at least one value)."""
        assay = pd.DataFrame(
            {
                DhConfig.holeid: ["DH001", "DH001", "DH002"],
                DhConfig.depth: [10.0, 40.0, 50.0],
                "CU_PPM": [500.0, np.nan, np.nan],
                "AU_PPM": [np.nan, np.nan, np.nan],
            }
        )
        database.add_point_table("assay", assay)

        # Keep rows with at least 1/2 (50%) valid values
        filtered_db = database.filter_by_nan_threshold("assay", ["CU_PPM", "AU_PPM"], threshold=0.5)

        # Only row 0 has at least 50% valid (1/2)
        assert len(filtered_db.points["assay"]) == 1
        assert filtered_db.points["assay"][DhConfig.depth].values[0] == 10.0

    def test_filter_by_nan_threshold_chainable(self, database):
        """Test that filter_by_nan_threshold can be chained."""
        assay = pd.DataFrame(
            {
                DhConfig.holeid: ["DH001", "DH001", "DH002", "DH003"],
                DhConfig.depth: [10.0, 40.0, 50.0, 100.0],
                "CU_PPM": [500.0, np.nan, 1200.0, 800.0],
                "AU_PPM": [0.5, np.nan, 0.8, 0.9],
            }
        )
        database.add_point_table("assay", assay)

        # Chain with filter method
        filtered_db = database.filter(holes=["DH001", "DH002"]).filter_by_nan_threshold(
            "assay", ["CU_PPM", "AU_PPM"], threshold=1.0
        )

        # Should have DH001 row 0 and DH002 row 2 (DH003 filtered out by holes filter)
        assert len(filtered_db.points["assay"]) == 2
        assert set(filtered_db.list_holes()) == {"DH001", "DH002"}

    def test_filter_by_nan_threshold_interval_table(self, database):
        """Test filtering works on interval tables."""
        geology = pd.DataFrame(
            {
                DhConfig.holeid: ["DH001", "DH002", "DH003"],
                DhConfig.sample_from: [0.0, 0.0, 0.0],
                DhConfig.sample_to: [30.0, 50.0, 80.0],
                "GRADE1": [5.5, np.nan, 3.2],
                "GRADE2": [2.1, np.nan, 4.5],
            }
        )
        database.add_interval_table("geology", geology)

        # Keep rows with at least 50% valid values
        filtered_db = database.filter_by_nan_threshold(
            "geology", ["GRADE1", "GRADE2"], threshold=0.5, table_type="interval"
        )

        # Rows 0 and 2 should remain (DH002 has 0/2 valid)
        assert len(filtered_db.intervals["geology"]) == 2
        assert "DH002" not in filtered_db.intervals["geology"][DhConfig.holeid].values

    def test_filter_by_nan_threshold_invalid_threshold(self, database):
        """Test that invalid threshold values raise error."""
        assay = pd.DataFrame(
            {DhConfig.holeid: ["DH001"], DhConfig.depth: [10.0], "CU_PPM": [500.0]}
        )
        database.add_point_table("assay", assay)

        with pytest.raises(ValueError, match="threshold must be between"):
            database.filter_by_nan_threshold("assay", ["CU_PPM"], threshold=1.5)

        with pytest.raises(ValueError, match="threshold must be between"):
            database.filter_by_nan_threshold("assay", ["CU_PPM"], threshold=-0.1)

    def test_filter_by_nan_threshold_missing_columns(self, database):
        """Test behavior with missing columns."""
        assay = pd.DataFrame(
            {DhConfig.holeid: ["DH001"], DhConfig.depth: [10.0], "CU_PPM": [500.0]}
        )
        database.add_point_table("assay", assay)

        # Should raise error if no columns exist
        with pytest.raises(ValueError, match="None of the specified columns found"):
            database.filter_by_nan_threshold("assay", ["MISSING1", "MISSING2"], threshold=0.5)

    def test_filter_by_nan_threshold_empty_result(self, database):
        """Test that empty result returns empty database."""
        assay = pd.DataFrame(
            {
                DhConfig.holeid: ["DH001"],
                DhConfig.depth: [10.0],
                "CU_PPM": [np.nan],
                "AU_PPM": [np.nan],
            }
        )
        database.add_point_table("assay", assay)

        # Filter with threshold that can't be met
        filtered_db = database.filter_by_nan_threshold("assay", ["CU_PPM", "AU_PPM"], threshold=0.5)

        # Should return empty database
        assert len(filtered_db.collar) == 0
        assert len(filtered_db.survey) == 0

    def test_combined_preprocessing_workflow(self, database, assay_with_mixed_data):
        """Test a complete preprocessing workflow combining both methods."""
        database.add_point_table("assay", assay_with_mixed_data)

        # Step 1: Validate and clean numerical columns
        database.validate_numerical_columns(
            "assay", ["CU_PPM", "AU_PPM", "AG_PPM"], allow_negative=False
        )

        # Step 2: Filter by NaN threshold (at least 67% valid means > 0.66)
        filtered_db = database.filter_by_nan_threshold(
            "assay", ["CU_PPM", "AU_PPM", "AG_PPM"], threshold=0.67
        )

        # Verify the result
        # After validation:
        # Row 0: CU=500, AU=0.5, AG=10 (3/3 = 100% valid) - keep
        # Row 1: CU=NaN, AU=1.2, AG=20 (2/3 = 66.7% valid) - remove (< 67%)
        # Row 2: CU=NaN, AU=NaN, AG=NaN (0/3 = 0% valid) - remove
        # Row 3: CU=1200, AU=0.8, AG=15 (3/3 = 100% valid) - keep
        # Row 4: CU=800, AU=NaN, AG=25 (2/3 = 66.7% valid) - remove (< 67%)

        assert len(filtered_db.points["assay"]) == 2
        depths = filtered_db.points["assay"][DhConfig.depth].values
        assert 10.0 in depths  # Row 0
        assert 80.0 in depths  # Row 3


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
