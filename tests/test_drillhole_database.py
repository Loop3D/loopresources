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
    
    @pytest.fixture
    def irregular_lithology(self):
        """Create irregular lithology data for resampling tests."""
        return pd.DataFrame({
            DhConfig.holeid: ['DH001', 'DH001', 'DH001', 'DH001'],
            DhConfig.sample_from: [0.0, 10.0, 25.0, 50.0],
            DhConfig.sample_to: [10.0, 25.0, 50.0, 100.0],
            'LITHO': ['Granite', 'Schist', 'Granite', 'Sandstone']
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


class TestIntervalResampling:
    """Test suite for interval resampling functionality."""
    
    @pytest.fixture
    def sample_collar(self):
        """Create sample collar data."""
        return pd.DataFrame({
            DhConfig.holeid: ['DH001'],
            DhConfig.x: [100.0],
            DhConfig.y: [1000.0],
            DhConfig.z: [50.0],
            DhConfig.total_depth: [100.0]
        })
    
    @pytest.fixture
    def sample_survey(self):
        """Create sample survey data."""
        return pd.DataFrame({
            DhConfig.holeid: ['DH001', 'DH001'],
            DhConfig.depth: [0.0, 50.0],
            DhConfig.azimuth: [0.0, 0.0],
            DhConfig.dip: [90.0, 90.0]
        })
    
    @pytest.fixture
    def irregular_lithology(self):
        """Create irregular lithology data for resampling tests."""
        return pd.DataFrame({
            DhConfig.holeid: ['DH001', 'DH001', 'DH001', 'DH001'],
            DhConfig.sample_from: [0.0, 10.0, 25.0, 50.0],
            DhConfig.sample_to: [10.0, 25.0, 50.0, 100.0],
            'LITHO': ['Granite', 'Schist', 'Granite', 'Sandstone']
        })
    
    def test_resample_interval_to_new_interval_basic(self, irregular_lithology):
        """Test basic interval resampling."""
        resampled = resample_interval_to_new_interval(
            irregular_lithology, ['LITHO'], new_interval=1.0
        )
        
        # Should have 100 intervals (0-100m at 1m spacing)
        assert len(resampled) == 100
        
        # Check first interval is Granite (0-10m range)
        assert resampled.iloc[0]['LITHO'] == 'Granite'
        
        # Check interval at 15m is Schist (10-25m range)
        assert resampled.iloc[15]['LITHO'] == 'Schist'
        
        # Check interval at 30m is Granite (25-50m range)
        assert resampled.iloc[30]['LITHO'] == 'Granite'
        
        # Check interval at 60m is Sandstone (50-100m range)
        assert resampled.iloc[60]['LITHO'] == 'Sandstone'
    
    def test_resample_interval_to_new_interval_5m(self, irregular_lithology):
        """Test interval resampling with 5m intervals."""
        resampled = resample_interval_to_new_interval(
            irregular_lithology, ['LITHO'], new_interval=5.0
        )
        
        # Should have 20 intervals (0-100m at 5m spacing)
        assert len(resampled) == 20
        
        # Check 0-5m is Granite
        assert resampled.iloc[0]['LITHO'] == 'Granite'
        
        # Check 10-15m is Schist
        assert resampled.iloc[2]['LITHO'] == 'Schist'
        
        # Check 50-55m is Sandstone
        assert resampled.iloc[10]['LITHO'] == 'Sandstone'
    
    def test_resample_interval_mode_selection(self):
        """Test that mode selection picks the value with biggest occurrence."""
        # Create data where one interval spans multiple lithologies
        data = pd.DataFrame({
            DhConfig.holeid: ['DH001', 'DH001', 'DH001'],
            DhConfig.sample_from: [0.0, 2.0, 7.0],
            DhConfig.sample_to: [2.0, 7.0, 10.0],
            'LITHO': ['A', 'B', 'C']
        })
        
        resampled = resample_interval_to_new_interval(
            data, ['LITHO'], new_interval=5.0
        )
        
        # First 5m interval (0-5m) should be 'B' (has 3m vs 2m for 'A')
        assert resampled.iloc[0]['LITHO'] == 'B'
        
        # Second 5m interval (5-10m) should be 'B' (2m) or 'C' (3m) - should be 'C'
        assert resampled.iloc[1]['LITHO'] == 'C'
    
    def test_drillhole_resample_method(self, sample_collar, sample_survey, irregular_lithology):
        """Test the DrillHole.resample() method."""
        db = DrillholeDatabase(sample_collar, sample_survey)
        db.add_interval_table('lithology', irregular_lithology)
        
        hole = db['DH001']
        resampled = hole.resample('lithology', ['LITHO'], new_interval=1.0)
        
        # Should have 100 intervals
        assert len(resampled) == 100
        
        # Check some key values
        assert resampled.iloc[0]['LITHO'] == 'Granite'
        assert resampled.iloc[15]['LITHO'] == 'Schist'
        assert resampled.iloc[60]['LITHO'] == 'Sandstone'
    
    def test_empty_table_handling(self):
        """Test that empty tables are handled gracefully."""
        empty_df = pd.DataFrame(columns=[DhConfig.sample_from, DhConfig.sample_to, 'LITHO'])
        
        resampled = resample_interval_to_new_interval(
            empty_df, ['LITHO'], new_interval=1.0
        )
        
        # Should return empty DataFrame
        assert len(resampled) == 0


if __name__ == '__main__':
    pytest.main([__file__])
