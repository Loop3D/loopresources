"""
Tests for file-based database backend functionality.

Tests the SQLite backend implementation for DrillholeDatabase.
"""

import pytest
import pandas as pd
import tempfile
import os

from loopresources.drillhole.drillhole_database import DrillholeDatabase
from loopresources.drillhole.dbconfig import DbConfig
from loopresources.drillhole.dhconfig import DhConfig


class TestDbConfig:
    """Test suite for DbConfig class."""

    def test_memory_backend_default(self):
        """Test default memory backend configuration."""
        config = DbConfig()
        assert config.backend == "memory"
        assert config.db_path is None
        assert config.project_name is None

    def test_file_backend_requires_path(self):
        """Test that file backend requires db_path."""
        with pytest.raises(ValueError, match="db_path is required"):
            DbConfig(backend="file")

    def test_invalid_backend(self):
        """Test that invalid backend raises error."""
        with pytest.raises(ValueError, match="Invalid backend"):
            DbConfig(backend="invalid")

    def test_file_backend_with_path(self):
        """Test file backend with path."""
        config = DbConfig(backend="file", db_path="/tmp/test.db")
        assert config.backend == "file"
        assert config.db_path == "/tmp/test.db"

    def test_project_name(self):
        """Test project name configuration."""
        config = DbConfig(backend="file", db_path="/tmp/test.db", project_name="test_project")
        assert config.project_name == "test_project"


class TestFileDatabaseBackend:
    """Test suite for file-based database backend."""

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
    def temp_db_path(self):
        """Create a temporary database path."""
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
            db_path = f.name
        yield db_path
        # Cleanup
        if os.path.exists(db_path):
            os.unlink(db_path)

    def test_memory_backend_basic(self, sample_collar, sample_survey):
        """Test basic memory backend functionality."""
        db = DrillholeDatabase(sample_collar, sample_survey)
        assert db.db_config.backend == "memory"
        assert len(db.collar) == 3
        assert len(db.survey) == 5

    def test_file_backend_initialization(self, sample_collar, sample_survey, temp_db_path):
        """Test file backend initialization."""
        db_config = DbConfig(backend="file", db_path=temp_db_path)
        db = DrillholeDatabase(sample_collar, sample_survey, db_config)

        assert db.db_config.backend == "file"
        assert os.path.exists(temp_db_path)

    def test_file_backend_data_persistence(self, sample_collar, sample_survey, temp_db_path):
        """Test that data persists in file backend."""
        db_config = DbConfig(backend="file", db_path=temp_db_path)
        db = DrillholeDatabase(sample_collar, sample_survey, db_config)

        # Access data to verify it's stored
        collar_data = db.collar
        survey_data = db.survey

        assert len(collar_data) == 3
        assert len(survey_data) == 5
        assert list(collar_data[DhConfig.holeid]) == ["DH001", "DH002", "DH003"]

    def test_save_to_database(self, sample_collar, sample_survey, temp_db_path):
        """Test saving database to file."""
        # Create memory database
        db = DrillholeDatabase(sample_collar, sample_survey)

        # Save to file
        db.save_to_database(temp_db_path)

        assert os.path.exists(temp_db_path)

    def test_load_from_database(self, sample_collar, sample_survey, temp_db_path):
        """Test loading database from file."""
        # Create and save database
        db1 = DrillholeDatabase(sample_collar, sample_survey)
        db1.save_to_database(temp_db_path)

        # Load from file
        db2 = DrillholeDatabase.from_database(temp_db_path)

        assert len(db2.collar) == 3
        assert len(db2.survey) == 5
        assert list(db2.collar[DhConfig.holeid]) == ["DH001", "DH002", "DH003"]

    def test_project_based_storage(self, sample_collar, sample_survey, temp_db_path):
        """Test project-based database storage."""
        # Create database with project
        db_config = DbConfig(backend="file", db_path=temp_db_path, project_name="project1")
        _db1 = DrillholeDatabase(sample_collar, sample_survey, db_config)

        # Create another database with different project
        sample_collar2 = sample_collar.copy()
        sample_collar2[DhConfig.holeid] = ["DH004", "DH005", "DH006"]
        sample_survey2 = sample_survey.copy()
        sample_survey2[DhConfig.holeid] = ["DH004", "DH004", "DH005", "DH005", "DH006"]

        db_config2 = DbConfig(backend="file", db_path=temp_db_path, project_name="project2")
        _db2 = DrillholeDatabase(sample_collar2, sample_survey2, db_config2)

        # Load project1 and verify
        db_loaded1 = DrillholeDatabase.from_database(temp_db_path, project_name="project1")
        assert list(db_loaded1.collar[DhConfig.holeid]) == ["DH001", "DH002", "DH003"]

        # Load project2 and verify
        db_loaded2 = DrillholeDatabase.from_database(temp_db_path, project_name="project2")
        assert list(db_loaded2.collar[DhConfig.holeid]) == ["DH004", "DH005", "DH006"]

    def test_save_with_project_name(self, sample_collar, sample_survey, temp_db_path):
        """Test saving with project name."""
        # Create memory database
        db = DrillholeDatabase(sample_collar, sample_survey)

        # Save with project name
        db.save_to_database(temp_db_path, project_name="my_project")

        # Load and verify
        db_loaded = DrillholeDatabase.from_database(temp_db_path, project_name="my_project")
        assert len(db_loaded.collar) == 3

    def test_link_to_database(self, sample_collar, sample_survey, temp_db_path):
        """Test linking to existing database."""
        # Create and save database
        db1 = DrillholeDatabase(sample_collar, sample_survey)
        db1.save_to_database(temp_db_path, project_name="linked_project")

        # Link to database
        db2 = DrillholeDatabase.link_to_database(temp_db_path, project_name="linked_project")

        assert len(db2.collar) == 3
        assert len(db2.survey) == 5

    def test_overwrite_project(self, sample_collar, sample_survey, temp_db_path):
        """Test overwriting existing project data."""
        # Save initial data
        db1 = DrillholeDatabase(sample_collar, sample_survey)
        db1.save_to_database(temp_db_path, project_name="test_project")

        # Create new data
        new_collar = sample_collar.copy()
        new_collar[DhConfig.holeid] = ["DH010", "DH011", "DH012"]
        new_survey = sample_survey.copy()
        new_survey[DhConfig.holeid] = ["DH010", "DH010", "DH011", "DH011", "DH012"]

        # Overwrite
        db2 = DrillholeDatabase(new_collar, new_survey)
        db2.save_to_database(temp_db_path, project_name="test_project", overwrite=True)

        # Load and verify
        db_loaded = DrillholeDatabase.from_database(temp_db_path, project_name="test_project")
        assert list(db_loaded.collar[DhConfig.holeid]) == ["DH010", "DH011", "DH012"]

    def test_nonexistent_project_raises_error(self, temp_db_path):
        """Test that loading nonexistent project raises error."""
        # Create empty database
        _db_config = DbConfig(backend="file", db_path=temp_db_path)

        with pytest.raises(ValueError, match="Projects table not found|Project .* not found"):
            DrillholeDatabase.from_database(temp_db_path, project_name="nonexistent")

    def test_interval_and_point_tables(self, sample_collar, sample_survey, temp_db_path):
        """Test saving and loading interval and point tables."""
        # Create database with interval and point data
        db = DrillholeDatabase(sample_collar, sample_survey)

        # Add interval table
        geology = pd.DataFrame(
            {
                DhConfig.holeid: ["DH001", "DH001", "DH002"],
                DhConfig.sample_from: [0.0, 30.0, 0.0],
                DhConfig.sample_to: [30.0, 80.0, 100.0],
                "LITHO": ["granite", "schist", "granite"],
            }
        )
        db.add_interval_table("geology", geology)

        # Add point table
        assay = pd.DataFrame(
            {
                DhConfig.holeid: ["DH001", "DH002"],
                DhConfig.depth: [10.0, 50.0],
                "CU_PPM": [500.0, 800.0],
            }
        )
        db.add_point_table("assay", assay)

        # Save to database
        db.save_to_database(temp_db_path, project_name="test_project")

        # Load and verify
        db_loaded = DrillholeDatabase.from_database(temp_db_path, project_name="test_project")

        # Verify basic structure
        assert len(db_loaded.collar) == 3
        assert len(db_loaded.survey) == 5

    def test_iteration_with_file_backend(self, sample_collar, sample_survey, temp_db_path):
        """Test iteration over drillholes with file backend."""
        from loopresources.drillhole.drillhole_database import DrillHole

        # Create database with file backend
        db_config = DbConfig(backend="file", db_path=temp_db_path)
        db = DrillholeDatabase(sample_collar, sample_survey, db_config=db_config)

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

    def test_sorted_by_with_file_backend(self, sample_collar, sample_survey, temp_db_path):
        """Test sorting drillholes with file backend."""

        # Create database with file backend
        db_config = DbConfig(backend="file", db_path=temp_db_path)
        db = DrillholeDatabase(sample_collar, sample_survey, db_config=db_config)

        # Sort by DEPTH (descending)
        hole_ids = [h.hole_id for h in db.sorted_by("DEPTH", reverse=True)]
        assert hole_ids == ["DH003", "DH002", "DH001"]

        # Sort by EAST (ascending)
        hole_ids = [h.hole_id for h in db.sorted_by("EAST")]
        assert hole_ids == ["DH001", "DH002", "DH003"]

        # Default sort by hole_id
        hole_ids = [h.hole_id for h in db.sorted_by()]
        assert hole_ids == ["DH001", "DH002", "DH003"]
