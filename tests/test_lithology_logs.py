"""
Tests for LithologyLogs class.

Tests the preprocessing tools for lithological drillhole data.
"""

import pytest
import pandas as pd
import numpy as np
from loopresources.drillhole.drillhole_database import DrillholeDatabase
from loopresources.drillhole.dhconfig import DhConfig
from loopresources.analysis import LithologyLogs


class TestLithologyLogs:
    """Test suite for LithologyLogs class."""

    @pytest.fixture
    def sample_collar(self):
        """Create sample collar data."""
        return pd.DataFrame(
            {
                DhConfig.holeid: ["DH001", "DH002", "DH003"],
                DhConfig.x: [100.0, 200.0, 300.0],
                DhConfig.y: [1000.0, 2000.0, 3000.0],
                DhConfig.z: [50.0, 60.0, 70.0],
                DhConfig.total_depth: [150.0, 200.0, 180.0],
            }
        )

    @pytest.fixture
    def sample_survey(self):
        """Create sample survey data."""
        return pd.DataFrame(
            {
                DhConfig.holeid: ["DH001", "DH001", "DH002", "DH002", "DH003"],
                DhConfig.depth: [0.0, 75.0, 0.0, 100.0, 0.0],
                DhConfig.azimuth: [0.0, 0.0, 45.0, 45.0, 90.0],
                DhConfig.dip: [90.0, 90.0, 80.0, 80.0, 85.0],
            }
        )

    @pytest.fixture
    def sample_geology(self):
        """Create sample geology interval data with multiple lithologies."""
        return pd.DataFrame(
            {
                DhConfig.holeid: [
                    "DH001",
                    "DH001",
                    "DH001",
                    "DH002",
                    "DH002",
                    "DH002",
                    "DH003",
                    "DH003",
                ],
                DhConfig.sample_from: [0.0, 30.0, 80.0, 0.0, 40.0, 90.0, 0.0, 50.0],
                DhConfig.sample_to: [30.0, 80.0, 120.0, 40.0, 90.0, 150.0, 50.0, 120.0],
                "LITHO": [
                    "granite",
                    "schist",
                    "granite",
                    "sandstone",
                    "schist",
                    "granite",
                    "granite",
                    "schist",
                ],
            }
        )

    @pytest.fixture
    def database_with_geology(self, sample_collar, sample_survey, sample_geology):
        """Create a DrillholeDatabase with geology data."""
        db = DrillholeDatabase(sample_collar, sample_survey)
        db.add_interval_table("geology", sample_geology)
        return db

    def test_initialization_success(self, database_with_geology):
        """Test successful initialization of LithologyLogs."""
        litho_logs = LithologyLogs(database_with_geology, "geology")

        assert litho_logs.database == database_with_geology
        assert litho_logs.interval_table_name == "geology"
        assert litho_logs.lithology_column == "LITHO"

    def test_initialization_custom_column(self, database_with_geology):
        """Test initialization with custom lithology column."""
        # Rename column for test
        table = database_with_geology.intervals["geology"].copy()
        table["ROCK_TYPE"] = table["LITHO"]
        database_with_geology.intervals["geology_custom"] = table

        litho_logs = LithologyLogs(
            database_with_geology, "geology_custom", lithology_column="ROCK_TYPE"
        )

        assert litho_logs.lithology_column == "ROCK_TYPE"

    def test_initialization_missing_table(self, database_with_geology):
        """Test initialization with non-existent table raises error."""
        with pytest.raises(ValueError, match="Interval table 'nonexistent' not found"):
            LithologyLogs(database_with_geology, "nonexistent")

    def test_initialization_missing_column(self, database_with_geology):
        """Test initialization with missing lithology column raises error."""
        with pytest.raises(ValueError, match="Column 'NONEXISTENT' not found"):
            LithologyLogs(database_with_geology, "geology", lithology_column="NONEXISTENT")

    def test_extract_contacts(self, database_with_geology):
        """Test extraction of lithology contacts."""
        litho_logs = LithologyLogs(database_with_geology, "geology")
        contacts = litho_logs.extract_contacts()

        assert not contacts.empty
        assert DhConfig.holeid in contacts.columns
        assert DhConfig.depth in contacts.columns
        assert "LITHO_ABOVE" in contacts.columns
        assert "LITHO_BELOW" in contacts.columns

        # Check that we have the expected number of contacts
        # DH001: granite->schist at 30, schist->granite at 80 (2 contacts)
        # DH002: sandstone->schist at 40, schist->granite at 90 (2 contacts)
        # DH003: granite->schist at 50 (1 contact)
        # Total: 5 contacts
        assert len(contacts) == 5

        # Verify first contact in DH001
        dh001_contacts = contacts[contacts[DhConfig.holeid] == "DH001"]
        assert len(dh001_contacts) == 2
        first_contact = dh001_contacts.iloc[0]
        assert first_contact[DhConfig.depth] == 30.0
        assert first_contact["LITHO_ABOVE"] == "granite"
        assert first_contact["LITHO_BELOW"] == "schist"

    def test_extract_contacts_store(self, database_with_geology):
        """Test extraction of contacts with storage."""
        litho_logs = LithologyLogs(database_with_geology, "geology")
        contacts = litho_logs.extract_contacts(store_as="contacts")

        # Check that table was stored
        assert "contacts" in database_with_geology.points
        stored = database_with_geology.points["contacts"]
        assert len(stored) == len(contacts)
        pd.testing.assert_frame_equal(stored, contacts)

    def test_extract_basal_contacts(self, database_with_geology):
        """Test extraction of basal contacts with lithological order."""
        litho_logs = LithologyLogs(database_with_geology, "geology")

        # Define stratigraphic order from top to bottom
        lithology_order = ["granite", "schist"]

        basal_contacts = litho_logs.extract_basal_contacts(lithology_order)

        assert not basal_contacts.empty
        assert DhConfig.holeid in basal_contacts.columns
        assert DhConfig.depth in basal_contacts.columns
        assert "LITHO" in basal_contacts.columns

        # Verify that all lithologies in basal contacts are in the order
        for _, contact in basal_contacts.iterrows():
            assert contact["LITHO"] in lithology_order, f"Lithology {contact['LITHO']} not in order"

    def test_extract_basal_contacts_store(self, database_with_geology):
        """Test extraction of basal contacts with storage."""
        litho_logs = LithologyLogs(database_with_geology, "geology")
        lithology_order = ["granite", "schist"]

        basal_contacts = litho_logs.extract_basal_contacts(
            lithology_order, store_as="basal_contacts"
        )

        # Check that table was stored
        assert "basal_contacts" in database_with_geology.points
        stored = database_with_geology.points["basal_contacts"]
        assert len(stored) == len(basal_contacts)

    def test_apply_smoothing_filter(self, database_with_geology):
        """Test application of smoothing filter."""
        litho_logs = LithologyLogs(database_with_geology, "geology")

        smoothed = litho_logs.apply_smoothing_filter(window_size=3)

        assert not smoothed.empty
        assert DhConfig.holeid in smoothed.columns
        assert DhConfig.sample_from in smoothed.columns
        assert DhConfig.sample_to in smoothed.columns
        assert "LITHO" in smoothed.columns

        # Check that we have the same number of intervals
        original = database_with_geology.intervals["geology"]
        assert len(smoothed) == len(original)

        # Check that depths have been smoothed (should be slightly different)
        original_depths = original[DhConfig.sample_from].values
        smoothed_depths = smoothed[DhConfig.sample_from].values
        # At least some depths should be different (interior points)
        assert not np.allclose(original_depths, smoothed_depths)

    def test_apply_smoothing_filter_store(self, database_with_geology):
        """Test smoothing filter with storage."""
        litho_logs = LithologyLogs(database_with_geology, "geology")

        smoothed = litho_logs.apply_smoothing_filter(window_size=3, store_as="geology_smoothed")

        # Check that table was stored
        assert "geology_smoothed" in database_with_geology.intervals
        stored = database_with_geology.intervals["geology_smoothed"]
        assert len(stored) == len(smoothed)

    def test_apply_smoothing_filter_small_window(self, database_with_geology):
        """Test smoothing with small window size."""
        litho_logs = LithologyLogs(database_with_geology, "geology")

        # Filter with window size of 1 should return similar to original
        smoothed = litho_logs.apply_smoothing_filter(window_size=1)

        assert not smoothed.empty
        original = database_with_geology.intervals["geology"]
        assert len(smoothed) == len(original)

    def test_identify_lithological_pairs(self, database_with_geology):
        """Test identification of lithological pairs."""
        litho_logs = LithologyLogs(database_with_geology, "geology")

        pairs = litho_logs.identify_lithological_pairs()

        assert not pairs.empty
        assert "LITHO_ABOVE" in pairs.columns
        assert "LITHO_BELOW" in pairs.columns
        assert "COUNT" in pairs.columns
        assert "HOLES" in pairs.columns

        # Check that pairs are sorted by count descending
        counts = pairs["COUNT"].values
        assert all(counts[i] >= counts[i + 1] for i in range(len(counts) - 1))

        # Verify expected pairs
        # granite->schist appears in DH001 and DH003
        granite_schist = pairs[
            (pairs["LITHO_ABOVE"] == "granite") & (pairs["LITHO_BELOW"] == "schist")
        ]
        assert len(granite_schist) > 0
        assert granite_schist.iloc[0]["COUNT"] >= 2

    def test_identify_lithological_pairs_store(self, database_with_geology):
        """Test identification of pairs with storage."""
        litho_logs = LithologyLogs(database_with_geology, "geology")

        litho_logs.identify_lithological_pairs(store_as="litho_pairs")

        # Note: The summary pairs table is not stored, but contacts are
        assert "litho_pairs" in database_with_geology.points
        stored = database_with_geology.points["litho_pairs"]
        assert not stored.empty

    def test_empty_hole_handling(self, sample_collar, sample_survey):
        """Test handling of holes with no geology data."""
        db = DrillholeDatabase(sample_collar, sample_survey)

        # Add geology for only one hole
        geology = pd.DataFrame(
            {
                DhConfig.holeid: ["DH001"],
                DhConfig.sample_from: [0.0],
                DhConfig.sample_to: [30.0],
                "LITHO": ["granite"],
            }
        )
        db.add_interval_table("geology", geology)

        litho_logs = LithologyLogs(db, "geology")
        contacts = litho_logs.extract_contacts()

        # Should not have contacts (only one interval in the hole)
        assert len(contacts) == 0

    def test_single_lithology_hole(self, sample_collar, sample_survey):
        """Test handling of hole with single lithology (no contacts)."""
        db = DrillholeDatabase(sample_collar, sample_survey)

        # Add geology with single lithology
        geology = pd.DataFrame(
            {
                DhConfig.holeid: ["DH001", "DH001"],
                DhConfig.sample_from: [0.0, 50.0],
                DhConfig.sample_to: [50.0, 100.0],
                "LITHO": ["granite", "granite"],  # Same lithology
            }
        )
        db.add_interval_table("geology", geology)

        litho_logs = LithologyLogs(db, "geology")
        contacts = litho_logs.extract_contacts()

        # Should not have contacts (same lithology throughout)
        assert len(contacts) == 0
    @pytest.mark.skip(reason="Orientation calculation not yet implemented")
    def test_calculate_contact_orientations(self, database_with_geology):
        """Test calculation of contact orientations."""
        litho_logs = LithologyLogs(database_with_geology, "geology")

        # Calculate orientations with large radius to include multiple contacts
        # (test data has contacts ~1000-2000 units apart)
        orientations = litho_logs.calculate_contact_orientations(radius=2500.0)
        print(orientations)
        assert not orientations.empty
        assert DhConfig.holeid in orientations.columns
        assert DhConfig.depth in orientations.columns
        assert "x" in orientations.columns
        assert "y" in orientations.columns
        assert "z" in orientations.columns
        assert "nx" in orientations.columns
        assert "ny" in orientations.columns
        assert "nz" in orientations.columns
        assert "dip" in orientations.columns
        assert "azimuth" in orientations.columns
        assert "n_neighbors" in orientations.columns

        # Check that normal vectors are normalized
        for _, row in orientations.iterrows():
            normal_mag = np.sqrt(row["nx"] ** 2 + row["ny"] ** 2 + row["nz"] ** 2)
            assert np.isclose(normal_mag, 1.0, atol=1e-6)

        # Check that dip is in valid range [0, 90]
        assert all(orientations["dip"] >= 0)
        assert all(orientations["dip"] <= 90)

        # Check that azimuth is in valid range [0, 360)
        assert all(orientations["azimuth"] >= 0)
        assert all(orientations["azimuth"] < 360)
    @pytest.mark.skip(reason="Orientation calculation not yet implemented")
    def test_calculate_contact_orientations_auto_radius(self, database_with_geology):
        """Test calculation of orientations with automatic radius."""
        litho_logs = LithologyLogs(database_with_geology, "geology")

        # Should calculate radius automatically
        orientations = litho_logs.calculate_contact_orientations()

        # Should have some orientations
        assert not orientations.empty
        assert "n_neighbors" in orientations.columns
    @pytest.mark.skip(reason="Orientation calculation not yet implemented")
    def test_calculate_contact_orientations_store(self, database_with_geology):
        """Test calculation of orientations with storage."""
        litho_logs = LithologyLogs(database_with_geology, "geology")

        orientations = litho_logs.calculate_contact_orientations(
            radius=2500.0, store_as="contact_orientations"
        )

        # Check that table was stored
        assert "contact_orientations" in database_with_geology.points
        stored = database_with_geology.points["contact_orientations"]
        assert len(stored) == len(orientations)

    def test_calculate_contact_orientations_min_neighbors(self, database_with_geology):
        """Test that min_neighbors parameter is validated."""
        litho_logs = LithologyLogs(database_with_geology, "geology")

        # Should raise error for min_neighbors < 3
        with pytest.raises(ValueError, match="min_neighbors must be at least 3"):
            litho_logs.calculate_contact_orientations(min_neighbors=2)

    def test_calculate_contact_orientations_no_contacts(self, sample_collar, sample_survey):
        """Test handling when no contacts exist."""
        db = DrillholeDatabase(sample_collar, sample_survey)

        # Add geology with single lithology (no contacts)
        geology = pd.DataFrame(
            {
                DhConfig.holeid: ["DH001"],
                DhConfig.sample_from: [0.0],
                DhConfig.sample_to: [30.0],
                "LITHO": ["granite"],
            }
        )
        db.add_interval_table("geology", geology)

        litho_logs = LithologyLogs(db, "geology")
        orientations = litho_logs.calculate_contact_orientations()

        # Should return empty dataframe
        assert orientations.empty
