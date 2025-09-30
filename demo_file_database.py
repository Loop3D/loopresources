"""
Demo script for file-based database backend in DrillholeDatabase.

This script demonstrates:
1. Creating a database with file backend
2. Saving a database to SQLite
3. Loading from a database
4. Using project-based organization
5. Comparing memory vs file storage
"""

import pandas as pd
import tempfile
from pathlib import Path

from loopresources.drillhole import DrillholeDatabase, DbConfig, DhConfig


def create_sample_data():
    """Create sample drillhole data."""
    collar = pd.DataFrame({
        DhConfig.holeid: ['DH001', 'DH002', 'DH003'],
        DhConfig.x: [100.0, 200.0, 300.0],
        DhConfig.y: [1000.0, 2000.0, 3000.0],
        DhConfig.z: [50.0, 60.0, 70.0],
        DhConfig.total_depth: [100.0, 150.0, 200.0]
    })
    
    survey = pd.DataFrame({
        DhConfig.holeid: ['DH001', 'DH001', 'DH002', 'DH002', 'DH003'],
        DhConfig.depth: [0.0, 50.0, 0.0, 75.0, 0.0],
        DhConfig.azimuth: [0.0, 0.0, 45.0, 45.0, 90.0],
        DhConfig.dip: [90.0, 90.0, 80.0, 80.0, 85.0]
    })
    
    return collar, survey


def demo_memory_backend():
    """Demo 1: Using memory backend (default)."""
    print("=" * 60)
    print("Demo 1: Memory Backend (Default)")
    print("=" * 60)
    
    collar, survey = create_sample_data()
    
    # Create database with default memory backend
    db = DrillholeDatabase(collar, survey)
    
    print(f"Backend: {db.db_config.backend}")
    print(f"Number of holes: {len(db.list_holes())}")
    print(f"Holes: {db.list_holes()}")
    print()


def demo_file_backend():
    """Demo 2: Using file backend."""
    print("=" * 60)
    print("Demo 2: File Backend")
    print("=" * 60)
    
    collar, survey = create_sample_data()
    
    # Create temporary database file
    with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
        db_path = f.name
    
    try:
        # Create database with file backend
        db_config = DbConfig(backend='file', db_path=db_path)
        db = DrillholeDatabase(collar, survey, db_config)
        
        print(f"Backend: {db.db_config.backend}")
        print(f"Database path: {db_path}")
        print(f"File exists: {Path(db_path).exists()}")
        print(f"File size: {Path(db_path).stat().st_size} bytes")
        print(f"Number of holes: {len(db.list_holes())}")
        print()
    finally:
        # Cleanup
        if Path(db_path).exists():
            Path(db_path).unlink()


def demo_save_load():
    """Demo 3: Save and load database."""
    print("=" * 60)
    print("Demo 3: Save and Load Database")
    print("=" * 60)
    
    collar, survey = create_sample_data()
    
    # Create temporary database file
    with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
        db_path = f.name
    
    try:
        # Create memory database and save to file
        db1 = DrillholeDatabase(collar, survey)
        print(f"Original database - holes: {db1.list_holes()}")
        
        db1.save_to_database(db_path)
        print(f"Database saved to: {db_path}")
        
        # Load from file
        db2 = DrillholeDatabase.from_database(db_path)
        print(f"Loaded database - holes: {db2.list_holes()}")
        print(f"Data matches: {db1.list_holes() == db2.list_holes()}")
        print()
    finally:
        # Cleanup
        if Path(db_path).exists():
            Path(db_path).unlink()


def demo_projects():
    """Demo 4: Project-based organization."""
    print("=" * 60)
    print("Demo 4: Project-Based Organization")
    print("=" * 60)
    
    # Create two different datasets
    collar1, survey1 = create_sample_data()
    
    collar2 = collar1.copy()
    collar2[DhConfig.holeid] = ['DH010', 'DH011', 'DH012']
    survey2 = survey1.copy()
    survey2[DhConfig.holeid] = ['DH010', 'DH010', 'DH011', 'DH011', 'DH012']
    
    # Create temporary database file
    with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
        db_path = f.name
    
    try:
        # Save project 1
        db1 = DrillholeDatabase(collar1, survey1)
        db1.save_to_database(db_path, project_name='Project_A')
        print(f"Saved Project_A with holes: {db1.list_holes()}")
        
        # Save project 2 to same database
        db2 = DrillholeDatabase(collar2, survey2)
        db2.save_to_database(db_path, project_name='Project_B')
        print(f"Saved Project_B with holes: {db2.list_holes()}")
        
        # Load each project separately
        db_a = DrillholeDatabase.from_database(db_path, project_name='Project_A')
        print(f"Loaded Project_A - holes: {db_a.list_holes()}")
        
        db_b = DrillholeDatabase.from_database(db_path, project_name='Project_B')
        print(f"Loaded Project_B - holes: {db_b.list_holes()}")
        print()
    finally:
        # Cleanup
        if Path(db_path).exists():
            Path(db_path).unlink()


def demo_file_backend_with_project():
    """Demo 5: Create database with file backend and project."""
    print("=" * 60)
    print("Demo 5: File Backend with Project")
    print("=" * 60)
    
    collar, survey = create_sample_data()
    
    # Create temporary database file
    with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
        db_path = f.name
    
    try:
        # Create database with file backend and project
        db_config = DbConfig(
            backend='file',
            db_path=db_path,
            project_name='MyProject'
        )
        db = DrillholeDatabase(collar, survey, db_config)
        
        print(f"Backend: {db.db_config.backend}")
        print(f"Project: {db.db_config.project_name}")
        print(f"Holes: {db.list_holes()}")
        
        # Link to database
        db_linked = DrillholeDatabase.link_to_database(db_path, project_name='MyProject')
        print(f"Linked to database - holes: {db_linked.list_holes()}")
        print()
    finally:
        # Cleanup
        if Path(db_path).exists():
            Path(db_path).unlink()


if __name__ == "__main__":
    print("\nDrillholeDatabase File Backend Demo")
    print("=" * 60)
    print()
    
    demo_memory_backend()
    demo_file_backend()
    demo_save_load()
    demo_projects()
    demo_file_backend_with_project()
    
    print("=" * 60)
    print("Demo complete!")
    print("=" * 60)
