"""
Tests for DrillHoleDatabase class.

Tests the clean implementation following AGENTS.md specifications.
"""

import pytest
import pandas as pd
import numpy as np
from loopresources.drillhole.drillhole_database import DrillholeDatabase, DrillHole
from loopresources.drillhole.dhconfig import DhConfig


class TestDrillholeDatabase:
    """Test suite for DrillholeDatabase class."""
    
    @pytest.fixture
    def sample_collar(self):
        """Create sample collar data."""
        return pd.DataFrame({
            DhConfig.holeid: ['DH001', 'DH002', 'DH003'],
            DhConfig.x: [100.0, 200.0, 300.0],
            DhConfig.y: [1000.0, 2000.0, 3000.0],
            DhConfig.z: [50.0, 60.0, 70.0],
            DhConfig.total_depth: [100.0, 150.0, 200.0]
        })
    
    @pytest.fixture
    def sample_survey(self):
        """Create sample survey data."""
        return pd.DataFrame({
            DhConfig.holeid: ['DH001', 'DH001', 'DH002', 'DH002', 'DH003'],
            DhConfig.depth: [0.0, 50.0, 0.0, 75.0, 0.0],
            DhConfig.azimuth: [0.0, 0.0, 45.0, 45.0, 90.0],
            DhConfig.dip: [90.0, 90.0, 80.0, 80.0, 85.0]
        })
    
    @pytest.fixture
    def sample_geology(self):
        """Create sample geology interval data."""
        return pd.DataFrame({
            DhConfig.holeid: ['DH001', 'DH001', 'DH002', 'DH003'],
            DhConfig.sample_from: [0.0, 30.0, 0.0, 0.0],
            DhConfig.sample_to: [30.0, 80.0, 100.0, 150.0],
            'LITHO': ['granite', 'schist', 'granite', 'sandstone']
        })
    
    def test_basic_functionality(self, sample_collar, sample_survey, sample_geology):
        """Test basic database functionality."""
        db = DrillholeDatabase(sample_collar, sample_survey)
        
        assert len(db.collar) == 3
        assert len(db.survey) == 5
        assert len(db.intervals) == 0
        assert len(db.points) == 0
        
        # Test adding interval table
        db.add_interval_table('geology', sample_geology)
        assert 'geology' in db.intervals
        assert len(db.intervals['geology']) == 4
        
        # Test list holes
        holes = db.list_holes()
        assert holes == ['DH001', 'DH002', 'DH003']
        
        # Test extent
        xmin, xmax, ymin, ymax, zmin, zmax = db.extent()
        assert xmin == 100.0
        assert xmax == 300.0


if __name__ == '__main__':
    pytest.main([__file__])
