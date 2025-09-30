#!/usr/bin/env python3
"""
Demonstration of the LithologyLogs class for lithological data preprocessing.

This script shows how to use LithologyLogs to extract contacts, apply smoothing,
and identify lithological pairs.
"""

import pandas as pd
from loopresources.drillhole.drillhole_database import DrillholeDatabase
from loopresources.drillhole.dhconfig import DhConfig
from loopresources.analysis import LithologyLogs


def create_sample_data():
    """Create sample drillhole data with lithology logs."""
    
    # Create collar data
    collar = pd.DataFrame({
        DhConfig.holeid: ['DH001', 'DH002', 'DH003'],
        DhConfig.x: [100.0, 200.0, 300.0],
        DhConfig.y: [1000.0, 2000.0, 3000.0],
        DhConfig.z: [50.0, 60.0, 70.0],
        DhConfig.total_depth: [150.0, 200.0, 180.0]
    })
    
    # Create survey data
    survey = pd.DataFrame({
        DhConfig.holeid: ['DH001', 'DH001', 'DH002', 'DH002', 'DH003'],
        DhConfig.depth: [0.0, 75.0, 0.0, 100.0, 0.0],
        DhConfig.azimuth: [0.0, 0.0, 45.0, 45.0, 90.0],
        DhConfig.dip: [90.0, 90.0, 80.0, 80.0, 85.0]
    })
    
    # Create geology interval data with various lithologies
    geology = pd.DataFrame({
        DhConfig.holeid: ['DH001', 'DH001', 'DH001', 'DH001', 'DH002', 'DH002', 'DH002', 'DH003', 'DH003', 'DH003'],
        DhConfig.sample_from: [0.0, 25.0, 60.0, 95.0, 0.0, 40.0, 90.0, 0.0, 50.0, 100.0],
        DhConfig.sample_to: [25.0, 60.0, 95.0, 130.0, 40.0, 90.0, 150.0, 50.0, 100.0, 150.0],
        'LITHO': ['sandstone', 'granite', 'schist', 'granite', 'sandstone', 'schist', 'granite', 'granite', 'schist', 'limestone']
    })
    
    return collar, survey, geology


def main():
    """Demonstrate LithologyLogs functionality."""
    
    print("=== LithologyLogs Demonstration ===")
    print()
    
    # Create sample data
    collar, survey, geology = create_sample_data()
    
    # Initialize database
    print("1. Creating DrillholeDatabase...")
    db = DrillholeDatabase(collar, survey)
    db.add_interval_table('geology', geology)
    print(f"   Created database with {len(db.list_holes())} holes")
    print(f"   Added {len(geology)} geology intervals")
    print()
    
    # Initialize LithologyLogs
    print("2. Initializing LithologyLogs...")
    litho_logs = LithologyLogs(db, 'geology')
    print(f"   Analyzing table: {litho_logs.interval_table_name}")
    print(f"   Lithology column: {litho_logs.lithology_column}")
    print()
    
    # Extract all contacts
    print("3. Extracting lithology contacts...")
    contacts = litho_logs.extract_contacts(store_as='contacts')
    print(f"   Found {len(contacts)} lithology contacts")
    if len(contacts) > 0:
        print("\n   First 5 contacts:")
        print(contacts.head().to_string(index=False))
    print()
    
    # Extract basal contacts with stratigraphic order
    print("4. Extracting basal contacts...")
    lithology_order = ['sandstone', 'granite', 'schist', 'limestone']
    basal_contacts = litho_logs.extract_basal_contacts(lithology_order, store_as='basal_contacts')
    print(f"   Stratigraphic order: {' -> '.join(lithology_order)}")
    print(f"   Found {len(basal_contacts)} basal contacts")
    if len(basal_contacts) > 0:
        print("\n   Basal contacts:")
        print(basal_contacts.to_string(index=False))
    print()
    
    # Apply smoothing filter
    print("5. Applying smoothing filter...")
    smoothed = litho_logs.apply_smoothing_filter(window_size=3, store_as='geology_smoothed')
    print(f"   Applied moving average filter with window size 3")
    print(f"   Smoothed {len(smoothed)} intervals")
    
    # Compare original vs smoothed for first hole
    original = db.intervals['geology'][db.intervals['geology'][DhConfig.holeid] == 'DH001']
    smoothed_dh001 = smoothed[smoothed[DhConfig.holeid] == 'DH001']
    
    print("\n   Original intervals (DH001):")
    print(original[[DhConfig.holeid, DhConfig.sample_from, DhConfig.sample_to, 'LITHO']].to_string(index=False))
    print("\n   Smoothed intervals (DH001):")
    print(smoothed_dh001[[DhConfig.holeid, DhConfig.sample_from, DhConfig.sample_to, 'LITHO']].to_string(index=False))
    print()
    
    # Identify lithological pairs
    print("6. Identifying lithological pairs...")
    pairs = litho_logs.identify_lithological_pairs(store_as='litho_pairs')
    print(f"   Found {len(pairs)} unique lithology pairs")
    if len(pairs) > 0:
        print("\n   Most common pairs:")
        print(pairs.head().to_string(index=False))
    print()
    
    # Show stored tables
    print("7. Stored tables in database...")
    print(f"   Point tables: {list(db.points.keys())}")
    print(f"   Interval tables: {list(db.intervals.keys())}")
    print()
    
    print("=== Demonstration Complete ===")


if __name__ == '__main__':
    main()
