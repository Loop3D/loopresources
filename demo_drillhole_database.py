#!/usr/bin/env python3
"""
Demonstration of the new DrillHoleDatabase class.

This script shows the clean, modern API following AGENTS.md specifications.
"""

import pandas as pd
import numpy as np
from loopresources.drillhole.drillhole_database import DrillholeDatabase
from loopresources.drillhole.dhconfig import DhConfig


def create_sample_data():
    """Create sample drillhole data for demonstration."""
    
    # Create collar data
    collar = pd.DataFrame({
        DhConfig.holeid: ['DH001', 'DH002', 'DH003', 'DH004'],
        DhConfig.x: [100.0, 200.0, 300.0, 400.0],
        DhConfig.y: [1000.0, 2000.0, 3000.0, 4000.0],
        DhConfig.z: [50.0, 60.0, 70.0, 80.0],
        DhConfig.total_depth: [150.0, 200.0, 180.0, 220.0]
    })
    
    # Create survey data
    survey = pd.DataFrame({
        DhConfig.holeid: ['DH001', 'DH001', 'DH001', 'DH002', 'DH002', 'DH003', 'DH004'],
        DhConfig.depth: [0.0, 50.0, 100.0, 0.0, 100.0, 0.0, 0.0],
        DhConfig.azimuth: [0.0, 0.0, 0.0, 45.0, 45.0, 90.0, 135.0],
        DhConfig.dip: [90.0, 90.0, 90.0, 80.0, 80.0, 85.0, 75.0]
    })
    
    # Create geology interval data
    geology = pd.DataFrame({
        DhConfig.holeid: ['DH001', 'DH001', 'DH001', 'DH002', 'DH002', 'DH003', 'DH004'],
        DhConfig.sample_from: [0.0, 40.0, 80.0, 0.0, 60.0, 0.0, 0.0],
        DhConfig.sample_to: [40.0, 80.0, 120.0, 60.0, 120.0, 100.0, 150.0],
        'LITHO': ['granite', 'schist', 'granite', 'sandstone', 'granite', 'limestone', 'shale']
    })
    
    # Create assay point data
    assay = pd.DataFrame({
        DhConfig.holeid: ['DH001', 'DH001', 'DH002', 'DH003', 'DH004'],
        DhConfig.depth: [20.0, 60.0, 30.0, 50.0, 75.0],
        'CU_PPM': [500.0, 1200.0, 800.0, 300.0, 900.0],
        'AU_PPM': [0.5, 1.2, 0.8, 0.3, 1.0],
        'DENSITY': [2.7, 2.8, 2.6, 2.9, 2.5]
    })
    
    return collar, survey, geology, assay


def main():
    """Demonstrate DrillHoleDatabase functionality."""
    
    print("=== DrillHoleDatabase Demonstration ===")
    print()
    
    # Create sample data
    collar, survey, geology, assay = create_sample_data()
    
    # Initialize database
    print("1. Creating DrillHoleDatabase...")
    db = DrillholeDatabase(collar, survey)
    print(f"   Created database with {len(db.list_holes())} holes")
    print(f"   Holes: {db.list_holes()}")
    print()
    
    # Add data tables
    print("2. Adding data tables...")
    db.add_interval_table('geology', geology)
    db.add_point_table('assay', assay)
    print(f"   Added geology intervals: {len(db.intervals['geology'])} records")
    print(f"   Added assay points: {len(db.points['assay'])} records")
    print()
    
    # Validate data
    print("3. Validating database...")
    try:
        db.validate()
        print("   ✓ Validation passed")
    except ValueError as e:
        print(f"   ✗ Validation failed: {e}")
    print()
    
    # Show extent
    print("4. Database extent:")
    xmin, xmax, ymin, ymax, zmin, zmax = db.extent()
    print(f"   X: {xmin:.1f} - {xmax:.1f}")
    print(f"   Y: {ymin:.1f} - {ymax:.1f}")
    print(f"   Z: {zmin:.1f} - {zmax:.1f}")
    print()
    
    # Access individual hole
    print("5. Accessing individual hole (DH001)...")
    hole = db['DH001']
    print(f"   Hole ID: {hole.hole_id}")
    print(f"   Collar location: ({hole.collar.iloc[0][DhConfig.x]:.1f}, {hole.collar.iloc[0][DhConfig.y]:.1f}, {hole.collar.iloc[0][DhConfig.z]:.1f})")
    print(f"   Survey stations: {len(hole.survey)}")
    print()
    
    # Show hole data
    print("6. Hole data tables...")
    geology_data = hole['geology']
    assay_data = hole['assay']
    print(f"   Geology intervals: {len(geology_data)}")
    print(f"   Assay points: {len(assay_data)}")
    
    if len(geology_data) > 0:
        print("   Lithologies:", list(geology_data['LITHO']))
    print()
    
    # Generate trace
    print("7. Generating hole trace...")
    trace = hole.trace(step=20.0)
    print(f"   Trace points: {len(trace)}")
    print(f"   Trace columns: {list(trace.columns)}")
    print()
    
    # Filtering examples
    print("8. Filtering examples...")
    
    # Filter by holes
    subset1 = db.filter(holes=['DH001', 'DH002'])
    print(f"   Filtered to DH001,DH002: {len(subset1.list_holes())} holes")
    
    # Filter by bounding box
    subset2 = db.filter(bbox=(50.0, 250.0, 500.0, 2500.0))
    print(f"   Filtered by bbox: {len(subset2.list_holes())} holes")
    
    # Filter by depth range
    subset3 = db.filter(depth_range=(0.0, 100.0))
    print(f"   Filtered by depth 0-100m: {len(subset3.survey)} survey records")
    
    # Filter by lithology
    subset4 = db.filter(expr="LITHO == 'granite'")
    if 'geology' in subset4.intervals:
        granite_count = len(subset4.intervals['geology'])
        print(f"   Filtered to granite only: {granite_count} intervals")
    print()
    
    # Combined filtering
    print("9. Combined filtering...")
    filtered = db.filter(
        holes=['DH001', 'DH002'],
        depth_range=(0.0, 80.0),
        expr="LITHO == 'granite'"
    )
    print(f"   Combined filter results:")
    print(f"   - Holes: {len(filtered.list_holes())}")
    print(f"   - Max depth: {filtered.survey[DhConfig.depth].max():.1f}m")
    if 'geology' in filtered.intervals:
        print(f"   - Geology intervals: {len(filtered.intervals['geology'])}")
        print(f"   - Lithologies: {set(filtered.intervals['geology']['LITHO'])}")
    print()
    
    print("=== Demonstration Complete ===")


if __name__ == '__main__':
    main()
