#!/usr/bin/env python3
"""
Example: Using String Representations for Drillhole Data Exploration

This example demonstrates how the new __str__ and __repr__ methods make
it easy to explore and understand drillhole data interactively.
"""

import pandas as pd
import numpy as np
import sys
sys.path.insert(0, '/home/runner/work/loopresources/loopresources')

from loopresources.drillhole.drillhole_database import DrillholeDatabase
from loopresources.drillhole.dhconfig import DhConfig

print("=" * 80)
print("Example 1: Quick Database Overview")
print("=" * 80)

# Load data (in real scenario, you'd use from_csv)
collar = pd.DataFrame({
    DhConfig.holeid: ['RC001', 'RC002', 'RC003'],
    DhConfig.x: [100.0, 150.0, 200.0],
    DhConfig.y: [500.0, 550.0, 600.0],
    DhConfig.z: [100.0, 105.0, 110.0],
    DhConfig.total_depth: [120.0, 150.0, 180.0]
})

survey = pd.DataFrame({
    DhConfig.holeid: ['RC001', 'RC001', 'RC002', 'RC002', 'RC003'],
    DhConfig.depth: [0.0, 60.0, 0.0, 75.0, 0.0],
    DhConfig.azimuth: [45.0, 47.0, 90.0, 92.0, 135.0],
    DhConfig.dip: [60.0, 58.0, 65.0, 63.0, 70.0]
})

db = DrillholeDatabase(collar, survey)

# Quick check with repr()
print("\nQuick check (repr):")
print(repr(db))

print("\n" + "=" * 80)
print("Example 2: Adding Assay Data and Reviewing")
print("=" * 80)

assay = pd.DataFrame({
    DhConfig.holeid: ['RC001', 'RC001', 'RC002', 'RC003'],
    DhConfig.sample_from: [10.0, 60.0, 20.0, 30.0],
    DhConfig.sample_to: [20.0, 70.0, 30.0, 40.0],
    'AU_GPT': [0.5, 2.3, 1.1, 0.8],
    'CU_PCT': [0.12, 0.35, 0.18, 0.09]
})

db.add_interval_table('assay', assay)

# Now see the detailed view
print("\nDetailed database view (str):")
print(db)

print("\n" + "=" * 80)
print("Example 3: Examining Individual Drillholes")
print("=" * 80)

print("\nHole RC001 (quick check):")
hole1 = db['RC001']
print(repr(hole1))

print("\nHole RC001 (detailed analysis):")
print(hole1)

print("\n" + "=" * 80)
print("Example 4: Finding High-Grade Intervals")
print("=" * 80)

print("\nIterating through holes to find high-grade gold:")
for hole in db:
    assay_data = hole['assay']
    if not assay_data.empty:
        max_au = assay_data['AU_GPT'].max()
        if max_au > 1.0:
            print(f"\n{repr(hole)}")
            print(f"  Maximum Au: {max_au:.2f} g/t")

print("\n" + "=" * 80)
print("Example 5: Data Quality Check")
print("=" * 80)

# Add some data with nulls
geology = pd.DataFrame({
    DhConfig.holeid: ['RC001', 'RC002', 'RC003'],
    DhConfig.sample_from: [0.0, 0.0, 0.0],
    DhConfig.sample_to: [100.0, 120.0, 150.0],
    'ROCK_TYPE': ['Granite', 'Basalt', None],  # Note: RC003 has null
    'ALTERATION': ['None', 'Chlorite', 'Sericite']
})

db.add_interval_table('geology', geology)

print("\nHole RC003 with missing lithology data:")
hole3 = db['RC003']
print(hole3)

print("\n" + "=" * 80)
print("Example 6: Workflow Summary")
print("=" * 80)

print("""
Typical Interactive Workflow:
1. Load data: db = DrillholeDatabase.from_csv(...)
2. Quick check: repr(db) or just 'db' in Jupyter
3. Detailed view: print(db)
4. Examine specific hole: hole = db['DH001']
5. See hole details: print(hole)
6. Iterate and filter: for hole in db: ...
7. Make decisions based on statistics shown automatically!

No need to call specific methods to see what's in your data.
Everything is immediately visible and informative!
""")

print("\n" + "=" * 80)
print("Examples Complete!")
print("=" * 80)
