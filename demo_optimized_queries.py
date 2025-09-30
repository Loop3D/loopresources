"""
Demo showing optimized database queries for specific holes.

This demonstrates how the optimized query methods fetch only the data needed
for a specific hole, rather than loading entire tables into memory.
"""

import pandas as pd
import tempfile
import time
from loopresources.drillhole import DrillholeDatabase, DbConfig, DhConfig


def create_large_dataset(num_holes=100):
    """Create a dataset with many holes."""
    hole_ids = [f'DH{i:04d}' for i in range(1, num_holes + 1)]
    
    collar = pd.DataFrame({
        DhConfig.holeid: hole_ids,
        DhConfig.x: [100.0 * i for i in range(1, num_holes + 1)],
        DhConfig.y: [1000.0 * i for i in range(1, num_holes + 1)],
        DhConfig.z: [50.0 + i for i in range(num_holes)],
        DhConfig.total_depth: [100.0 + i * 10 for i in range(num_holes)]
    })
    
    # Create survey with multiple rows per hole
    survey_data = []
    for hole_id in hole_ids:
        survey_data.extend([
            {DhConfig.holeid: hole_id, DhConfig.depth: 0.0, DhConfig.azimuth: 0.0, DhConfig.dip: 90.0},
            {DhConfig.holeid: hole_id, DhConfig.depth: 50.0, DhConfig.azimuth: 0.0, DhConfig.dip: 90.0},
            {DhConfig.holeid: hole_id, DhConfig.depth: 100.0, DhConfig.azimuth: 0.0, DhConfig.dip: 90.0},
        ])
    
    survey = pd.DataFrame(survey_data)
    
    return collar, survey


def demo_optimized_queries():
    """Demonstrate optimized database queries."""
    print("=" * 70)
    print("Optimized Database Query Demo")
    print("=" * 70)
    
    # Create dataset with many holes
    num_holes = 100
    print(f"\nCreating dataset with {num_holes} holes...")
    collar, survey = create_large_dataset(num_holes)
    print(f"  Collar rows: {len(collar)}")
    print(f"  Survey rows: {len(survey)}")
    
    # Create temporary database
    with tempfile.NamedTemporaryFile(suffix='.db', delete=True) as f:
        db_path = f.name
    
    print(f"\nCreating file-based database at: {db_path}")
    db_config = DbConfig(backend='file', db_path=db_path, project_name='demo')
    db = DrillholeDatabase(collar, survey, db_config)
    
    # Demonstrate optimized query for single hole
    print("\n" + "=" * 70)
    print("Accessing Single Hole Data")
    print("=" * 70)
    
    hole_id = 'DH0050'
    print(f"\nAccessing data for hole: {hole_id}")
    
    # Using optimized method
    print("\nUsing optimized get_collar_for_hole():")
    start = time.time()
    collar_data = db.get_collar_for_hole(hole_id)
    elapsed = time.time() - start
    print(f"  Retrieved {len(collar_data)} row(s)")
    print(f"  Time: {elapsed*1000:.2f} ms")
    print(f"  Data: {collar_data[DhConfig.holeid].iloc[0]} at ({collar_data[DhConfig.x].iloc[0]}, {collar_data[DhConfig.y].iloc[0]})")
    
    print("\nUsing optimized get_survey_for_hole():")
    start = time.time()
    survey_data = db.get_survey_for_hole(hole_id)
    elapsed = time.time() - start
    print(f"  Retrieved {len(survey_data)} row(s)")
    print(f"  Time: {elapsed*1000:.2f} ms")
    
    # Demonstrate DrillHole class using optimized queries
    print("\n" + "=" * 70)
    print("DrillHole Class (uses optimized queries automatically)")
    print("=" * 70)
    
    print(f"\nCreating DrillHole instance for: {hole_id}")
    start = time.time()
    drillhole = db[hole_id]
    elapsed = time.time() - start
    print(f"  Time to initialize: {elapsed*1000:.2f} ms")
    print(f"  Collar rows: {len(drillhole.collar)}")
    print(f"  Survey rows: {len(drillhole.survey)}")
    
    # Show what SQL query would be executed
    print("\n" + "=" * 70)
    print("SQL Query Optimization")
    print("=" * 70)
    print("\nFor file backend, the query executed is:")
    print(f"  SELECT * FROM collar WHERE project_id = ? AND {DhConfig.holeid} = ?")
    print(f"  SELECT * FROM survey WHERE project_id = ? AND {DhConfig.holeid} = ?")
    print("\nThis fetches only the rows for the specific hole, not the entire table!")
    
    # Demonstrate with multiple holes
    print("\n" + "=" * 70)
    print("Accessing Multiple Holes Efficiently")
    print("=" * 70)
    
    hole_ids = ['DH0010', 'DH0030', 'DH0070']
    print(f"\nAccessing {len(hole_ids)} holes: {', '.join(hole_ids)}")
    
    start = time.time()
    for hid in hole_ids:
        drillhole = db[hid]
    elapsed = time.time() - start
    print(f"  Total time: {elapsed*1000:.2f} ms")
    print(f"  Average per hole: {elapsed*1000/len(hole_ids):.2f} ms")
    
    # Key benefits
    print("\n" + "=" * 70)
    print("Key Benefits of Optimized Queries")
    print("=" * 70)
    print("""
1. **Memory Efficiency**: Only loads data for the requested hole
2. **Performance**: Database does the filtering (faster than Python)
3. **Scalability**: Works efficiently even with massive datasets
4. **Automatic**: DrillHole class uses optimized queries automatically
5. **Backward Compatible**: Memory backend still works the same way
    """)
    
    print("=" * 70)
    print("Demo Complete!")
    print("=" * 70)


if __name__ == "__main__":
    demo_optimized_queries()
