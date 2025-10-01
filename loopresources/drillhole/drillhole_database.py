"""
DrillHoleDatabase - A clean implementation based on AGENTS.md specifications.

This module provides a modern, pandas-native interface for drillhole data management
with filtering, validation, and export capabilities.
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Tuple, Union, Callable
import logging
import sqlite3
import json
from pathlib import Path

from .dhconfig import DhConfig
from .dbconfig import DbConfig

logger = logging.getLogger(__name__)


class DrillHole:
    """
    A view of the DrillholeDatabase for a single HOLE_ID.
    Provides per-hole access, sampling, and visualization.
    """

    def __init__(self, database: "DrillholeDatabase", hole_id: str):
        """
        Initialize DrillHole view.

        Parameters
        ----------
        database : DrillholeDatabase
            Parent database instance
        hole_id : str
            The HOLE_ID for this view
        """
        self.database = database
        self.hole_id = hole_id

        # Use optimized methods to get data for this hole
        # For file backend, this queries the database directly
        self.collar = self.database.get_collar_for_hole(hole_id)
        self.survey = self.database.get_survey_for_hole(hole_id)

        if self.collar.empty:
            raise ValueError(f"Hole {hole_id} not found in collar data")
        if self.survey.empty:
            raise ValueError(f"Hole {hole_id} not found in survey data")

    def __getitem__(self, propertyname: str) -> pd.DataFrame:
        """
        Return a single interval or point table for this hole.

        Parameters
        ----------
        propertyname : str
            Name of the interval or point table

        Returns
        -------
        pd.DataFrame
            Filtered table containing only data for this hole
        """
        # Check intervals first
        if propertyname in self.database.intervals:
            return self.database.get_interval_data_for_hole(propertyname, self.hole_id)

        # Check points
        if propertyname in self.database.points:
            return self.database.get_point_data_for_hole(propertyname, self.hole_id)

        raise KeyError(f"Table '{propertyname}' not found in intervals or points")

    def interval_tables(self) -> Dict[str, pd.DataFrame]:
        """Return all interval tables for this hole."""
        result = {}
        for name in self.database.intervals.keys():
            filtered = self.database.get_interval_data_for_hole(name, self.hole_id)
            if not filtered.empty:
                result[name] = filtered
        return result

    def point_tables(self) -> Dict[str, pd.DataFrame]:
        """Return all point tables for this hole."""
        result = {}
        for name in self.database.points.keys():
            filtered = self.database.get_point_data_for_hole(name, self.hole_id)
            if not filtered.empty:
                result[name] = filtered
        return result

    def trace(self, step: float = 1.0) -> pd.DataFrame:
        """
        Return the interpolated XYZ trace of the hole.

        Parameters
        ----------
        step : float, default 1.0
            Step size for interpolation along hole depth

        Returns
        -------
        pd.DataFrame
            DataFrame with depth, x, y, z columns
        """
        from .desurvey import desurvey

        return desurvey(self.collar, self.survey, step)

    def depth_at(self, x: float, y: float, z: float) -> float:
        """
        Return depth along hole closest to a given XYZ point.

        Parameters
        ----------
        x, y, z : float
            Coordinates of the point

        Returns
        -------
        float
            Depth along hole closest to the point
        """
        trace = self.trace()
        distances = np.sqrt((trace["x"] - x) ** 2 + (trace["y"] - y) ** 2 + (trace["z"] - z) ** 2)
        closest_idx = distances.idxmin()
        return trace.loc[closest_idx, "depth"]

    def vtk(
        self, 
        newinterval: Union[float, np.ndarray] = 1.0, 
        radius: float = 0.1,
        properties: Optional[List[str]] = None
    ):
        """
        Return a PyVista tube object representing the drillhole trace.

        Parameters
        ----------
        newinterval : float or array-like, default 1.0
            Step size for interpolation along hole depth, or specific depths to sample
        radius : float, default 0.1
            Radius of the tube representation
        properties : list of str, optional
            List of property names (interval table names) to attach as cell data.
            Properties will be resampled to match the trace intervals.

        Returns
        -------
        pyvista.PolyData
            PyVista tube object of the drillhole trace with optional cell properties

        Examples
        --------
        >>> hole = db['DH001']
        >>> # Create VTK with lithology as cell property
        >>> tube = hole.vtk(newinterval=1.0, properties=['lithology'])
        """
        try:
            import pyvista as pv
        except ImportError:
            raise ImportError(
                "PyVista is required for VTK output. Install with: pip install pyvista"
            )

        trace = self.trace(newinterval)

        # Create line connectivity for PyVista
        line_connectivity = np.vstack(
            [
                np.zeros(len(trace) - 1, dtype=int) + 2,  # Each line segment has 2 points
                np.arange(0, len(trace) - 1),  # Start points
                np.arange(1, len(trace)),  # End points
            ]
        ).T

        # Create PolyData with points and line connectivity
        polydata = pv.PolyData(trace[["x", "y", "z"]].values, lines=line_connectivity)
        
        # Add properties as cell data if requested
        if properties is not None:
            from .resample import resample_interval
            
            for prop_name in properties:
                try:
                    # Get the interval table
                    prop_table = self[prop_name]
                    if prop_table.empty:
                        logger.warning(f"Property table '{prop_name}' is empty, skipping")
                        continue
                    
                    # Get all columns except the standard ones
                    cols_to_resample = [col for col in prop_table.columns 
                                       if col not in [DhConfig.holeid, DhConfig.sample_from, 
                                                     DhConfig.sample_to, DhConfig.depth]]
                    
                    if not cols_to_resample:
                        logger.warning(f"No data columns found in property table '{prop_name}', skipping")
                        continue
                    
                    # Resample the property to the trace points
                    trace_with_props = resample_interval(
                        trace, prop_table, cols_to_resample, method="direct"
                    )
                    
                    # Add each column as cell data (for line segments, not points)
                    # Cell data should have n-1 values for n points
                    for col in cols_to_resample:
                        if col in trace_with_props.columns:
                            # Use values from trace points, excluding the last one for cell data
                            cell_values = trace_with_props[col].values[:-1]
                            polydata.cell_data[f"{prop_name}_{col}"] = cell_values
                
                except KeyError:
                    logger.warning(f"Property table '{prop_name}' not found, skipping")
                except Exception as e:
                    logger.warning(f"Failed to add property '{prop_name}': {e}")

        # Return as tube
        return polydata.tube(radius=radius)

    def desurvey_intervals(self, interval_table_name: str) -> pd.DataFrame:
        """
        Desurvey interval data to get 3D coordinates for FROM and TO depths.

        Parameters
        ----------
        interval_table_name : str
            Name of the interval table to desurvey

        Returns
        -------
        pd.DataFrame
            Original interval data with added columns:
            - x_from, y_from, z_from: 3D coordinates at FROM depth
            - x_to, y_to, z_to: 3D coordinates at TO depth
            - x_mid, y_mid, z_mid: 3D coordinates at midpoint depth
        """
        # Get the interval table for this hole
        intervals = self[interval_table_name]

        if intervals.empty:
            return intervals

        # Get all unique depths (from and to values)
        from_depths = intervals[DhConfig.sample_from].values
        to_depths = intervals[DhConfig.sample_to].values
        all_depths = np.unique(np.concatenate([from_depths, to_depths]))

        # Desurvey at all depths
        from .desurvey import desurvey

        trace = desurvey(self.collar, self.survey, all_depths)

        # Create interpolators for x, y, z coordinates
        from scipy.interpolate import interp1d

        x_interp = interp1d(
            trace[DhConfig.depth], trace["x"], kind="linear", fill_value="extrapolate"
        )
        y_interp = interp1d(
            trace[DhConfig.depth], trace["y"], kind="linear", fill_value="extrapolate"
        )
        z_interp = interp1d(
            trace[DhConfig.depth], trace["z"], kind="linear", fill_value="extrapolate"
        )

        # Create result dataframe with original data
        result = intervals.copy()

        # Add FROM coordinates
        result["x_from"] = x_interp(from_depths)
        result["y_from"] = y_interp(from_depths)
        result["z_from"] = z_interp(from_depths)

        # Add TO coordinates
        result["x_to"] = x_interp(to_depths)
        result["y_to"] = y_interp(to_depths)
        result["z_to"] = z_interp(to_depths)

        # Add midpoint coordinates
        mid_depths = (from_depths + to_depths) / 2
        result["x_mid"] = x_interp(mid_depths)
        result["y_mid"] = y_interp(mid_depths)
        result["z_mid"] = z_interp(mid_depths)
        result["depth_mid"] = mid_depths

        return result

    def desurvey_points(self, point_table_name: str) -> pd.DataFrame:
        """
        Desurvey point data to get 3D coordinates.

        Parameters
        ----------
        point_table_name : str
            Name of the point table to desurvey

        Returns
        -------
        pd.DataFrame
            Original point data with added columns: x, y, z
        """
        # Get the point table for this hole
        points = self[point_table_name]

        if points.empty:
            return points

        # Get all depths
        depths = points[DhConfig.depth].values

        # Desurvey at these depths
        from .desurvey import desurvey

        trace = desurvey(self.collar, self.survey, depths)

        # Create result dataframe with original data
        result = points.copy()

        # Add coordinates
        result["x"] = trace["x"].values
        result["y"] = trace["y"].values
        result["z"] = trace["z"].values

        return result

    def resample(self, interval_table_name: str, cols: List[str], new_interval: float = 1.0) -> pd.DataFrame:
        """
        Resample interval data onto a new regular interval.
        
        For each new interval, finds all overlapping original intervals and 
        assigns the value that has the biggest occurrence (mode).
        
        Parameters
        ----------
        interval_table_name : str
            Name of the interval table to resample
        cols : list of str
            List of column names to resample
        new_interval : float, default 1.0
            Size of new regular intervals in meters
        
        Returns
        -------
        pd.DataFrame
            Resampled interval data with regular intervals
        
        Examples
        --------
        >>> hole = db['DH001']
        >>> # Resample lithology to 1m intervals
        >>> resampled = hole.resample('lithology', ['LITHO'], new_interval=1.0)
        """
        from .resample import resample_interval_to_new_interval
        
        # Get the interval table for this hole
        intervals = self[interval_table_name]
        
        if intervals.empty:
            return intervals
        
        # Resample the intervals
        return resample_interval_to_new_interval(intervals, cols, new_interval)


class DrillholeDatabase:
    """
    Main container for all drillhole data.

    Stores global data as pandas DataFrames and dictionaries following
    the specification in AGENTS.md.
    """

    def __init__(
        self,
        collar: pd.DataFrame,
        survey: pd.DataFrame,
        db_config: Optional[DbConfig] = None
    ):
        """
        Initialize DrillholeDatabase.

        Parameters
        ----------
        collar : pd.DataFrame
            Collar data with one row per drillhole
            Required columns: HOLE_ID, X, Y, Z, TOTAL_DEPTH
        survey : pd.DataFrame
            Survey data with one row per survey station
            Required columns: HOLE_ID, DEPTH, AZIMUTH, DIP
        db_config : DbConfig, optional
            Database backend configuration. If None, uses in-memory storage.
        """
        self.db_config = db_config if db_config is not None else DbConfig(backend='memory')
        self._conn = None
        
        # Store data based on backend configuration
        if self.db_config.backend == 'memory':
            self.collar = collar.copy()
            self.survey = survey.copy()
            self.intervals: Dict[str, pd.DataFrame] = {}
            self.points: Dict[str, pd.DataFrame] = {}
        else:
            # File-based backend
            self._initialize_database()
            self._store_data_to_db(collar, survey)
            # Keep references but data will be loaded from DB on demand
            self._collar = None
            self._survey = None
            self.intervals: Dict[str, pd.DataFrame] = {}
            self.points: Dict[str, pd.DataFrame] = {}

        # Validate input data
        self._validate_collar()
        self._validate_survey()

        # Convert angles if needed
        self._normalize_angles()
    
    @property
    def collar(self) -> pd.DataFrame:
        """Get collar data from memory or database."""
        if self.db_config.backend == 'memory':
            return self._collar if hasattr(self, '_collar') and self._collar is not None else getattr(self, '_memory_collar', pd.DataFrame())
        else:
            return self._load_table_from_db('collar')
    
    @collar.setter
    def collar(self, value: pd.DataFrame):
        """Set collar data."""
        if self.db_config.backend == 'memory':
            self._memory_collar = value
        else:
            self._collar = value
    
    @property
    def survey(self) -> pd.DataFrame:
        """Get survey data from memory or database."""
        if self.db_config.backend == 'memory':
            return self._survey if hasattr(self, '_survey') and self._survey is not None else getattr(self, '_memory_survey', pd.DataFrame())
        else:
            return self._load_table_from_db('survey')
    
    @survey.setter
    def survey(self, value: pd.DataFrame):
        """Set survey data."""
        if self.db_config.backend == 'memory':
            self._memory_survey = value
        else:
            self._survey = value
    
    def get_collar_for_hole(self, hole_id: str) -> pd.DataFrame:
        """
        Get collar data for a specific hole.
        
        For file backend, this queries the database directly rather than
        loading all collar data and filtering in Python.
        
        Parameters
        ----------
        hole_id : str
            The hole identifier
        
        Returns
        -------
        pd.DataFrame
            Collar data for the specified hole
        """
        if self.db_config.backend == 'memory':
            collar_data = self.collar
            mask = collar_data[DhConfig.holeid] == hole_id
            return collar_data[mask].copy()
        else:
            return self._load_table_from_db('collar', hole_id=hole_id)
    
    def get_survey_for_hole(self, hole_id: str) -> pd.DataFrame:
        """
        Get survey data for a specific hole.
        
        For file backend, this queries the database directly rather than
        loading all survey data and filtering in Python.
        
        Parameters
        ----------
        hole_id : str
            The hole identifier
        
        Returns
        -------
        pd.DataFrame
            Survey data for the specified hole
        """
        if self.db_config.backend == 'memory':
            survey_data = self.survey
            mask = survey_data[DhConfig.holeid] == hole_id
            return survey_data[mask].copy()
        else:
            return self._load_table_from_db('survey', hole_id=hole_id)
    
    def get_interval_data_for_hole(self, table_name: str, hole_id: str) -> pd.DataFrame:
        """
        Get interval table data for a specific hole.
        
        For file backend with saved tables, this could query the database directly.
        Currently filters in-memory data.
        
        Parameters
        ----------
        table_name : str
            Name of the interval table
        hole_id : str
            The hole identifier
        
        Returns
        -------
        pd.DataFrame
            Interval data for the specified hole
        """
        if table_name not in self.intervals:
            return pd.DataFrame()
        
        table = self.intervals[table_name]
        mask = table[DhConfig.holeid] == hole_id
        return table[mask].copy()
    
    def get_point_data_for_hole(self, table_name: str, hole_id: str) -> pd.DataFrame:
        """
        Get point table data for a specific hole.
        
        For file backend with saved tables, this could query the database directly.
        Currently filters in-memory data.
        
        Parameters
        ----------
        table_name : str
            Name of the point table
        hole_id : str
            The hole identifier
        
        Returns
        -------
        pd.DataFrame
            Point data for the specified hole
        """
        if table_name not in self.points:
            return pd.DataFrame()
        
        table = self.points[table_name]
        mask = table[DhConfig.holeid] == hole_id
        return table[mask].copy()
    
    def _initialize_database(self):
        """Initialize SQLite database and create tables."""
        db_path = Path(self.db_config.db_path)
        db_path.parent.mkdir(parents=True, exist_ok=True)
        
        self._conn = sqlite3.connect(str(db_path))
        cursor = self._conn.cursor()
        
        # Create projects table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS projects (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT UNIQUE NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                metadata TEXT
            )
        ''')
        
        # Insert project if specified
        if self.db_config.project_name:
            cursor.execute(
                'INSERT OR IGNORE INTO projects (name) VALUES (?)',
                (self.db_config.project_name,)
            )
        
        self._conn.commit()
    
    def _get_project_id(self) -> Optional[int]:
        """Get project ID from database."""
        if not self.db_config.project_name:
            return None
        
        cursor = self._conn.cursor()
        cursor.execute(
            'SELECT id FROM projects WHERE name = ?',
            (self.db_config.project_name,)
        )
        result = cursor.fetchone()
        return result[0] if result else None
    
    def _store_data_to_db(self, collar: pd.DataFrame, survey: pd.DataFrame):
        """Store collar and survey data to database."""
        project_id = self._get_project_id()
        
        # Add project_id column if project is specified
        if project_id is not None:
            collar = collar.copy()
            collar['project_id'] = project_id
            survey = survey.copy()
            survey['project_id'] = project_id
        
        # Store to SQLite
        collar.to_sql('collar', self._conn, if_exists='append', index=False)
        survey.to_sql('survey', self._conn, if_exists='append', index=False)
    
    def _load_table_from_db(self, table_name: str, hole_id: Optional[str] = None) -> pd.DataFrame:
        """
        Load table from database.
        
        Parameters
        ----------
        table_name : str
            Name of the table to load
        hole_id : str, optional
            If provided, only load data for this specific hole
        
        Returns
        -------
        pd.DataFrame
            Loaded data
        """
        if self._conn is None:
            return pd.DataFrame()
        
        project_id = self._get_project_id()
        
        # Build query with optional filters
        conditions = []
        params = []
        
        if project_id is not None:
            conditions.append("project_id = ?")
            params.append(project_id)
        
        if hole_id is not None:
            conditions.append(f"{DhConfig.holeid} = ?")
            params.append(hole_id)
        
        if conditions:
            where_clause = " WHERE " + " AND ".join(conditions)
            query = f"SELECT * FROM {table_name}{where_clause}"
            df = pd.read_sql_query(query, self._conn, params=tuple(params))
        else:
            df = pd.read_sql_query(f"SELECT * FROM {table_name}", self._conn)
        
        # Remove project_id column from result
        if 'project_id' in df.columns:
            df = df.drop(columns=['project_id'])
        
        return df
    
    @classmethod
    def from_database(
        cls,
        db_path: str,
        project_name: Optional[str] = None
    ) -> "DrillholeDatabase":
        """
        Load DrillholeDatabase from an existing SQLite database.
        
        Parameters
        ----------
        db_path : str
            Path to the SQLite database file
        project_name : str, optional
            Name of the project to load. If None, loads all data.
        
        Returns
        -------
        DrillholeDatabase
            Database instance loaded from file
        """
        db_config = DbConfig(backend='file', db_path=db_path, project_name=project_name)
        
        # Connect to database and load collar/survey
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Check if projects table exists
        cursor.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='projects'"
        )
        projects_table_exists = cursor.fetchone() is not None
        
        # Load collar and survey
        if project_name:
            if not projects_table_exists:
                conn.close()
                raise ValueError(f"Projects table not found in database")
            
            # Get project_id
            cursor.execute('SELECT id FROM projects WHERE name = ?', (project_name,))
            result = cursor.fetchone()
            if result is None:
                conn.close()
                raise ValueError(f"Project '{project_name}' not found in database")
            project_id = result[0]
            
            collar = pd.read_sql_query(
                "SELECT * FROM collar WHERE project_id = ?",
                conn,
                params=(project_id,)
            )
            survey = pd.read_sql_query(
                "SELECT * FROM survey WHERE project_id = ?",
                conn,
                params=(project_id,)
            )
            
            # Remove project_id from dataframes
            if 'project_id' in collar.columns:
                collar = collar.drop(columns=['project_id'])
            if 'project_id' in survey.columns:
                survey = survey.drop(columns=['project_id'])
        else:
            collar = pd.read_sql_query("SELECT * FROM collar", conn)
            survey = pd.read_sql_query("SELECT * FROM survey", conn)
        
        conn.close()
        
        # Create instance with loaded data
        instance = cls.__new__(cls)
        instance.db_config = db_config
        instance._conn = None
        instance._initialize_database()
        
        # Store data in memory for validation
        instance._memory_collar = collar
        instance._memory_survey = survey
        instance.intervals = {}
        instance.points = {}
        
        # Validate
        instance._validate_collar()
        instance._validate_survey()
        instance._normalize_angles()
        
        return instance
    
    @classmethod
    def link_to_database(
        cls,
        db_path: str,
        project_name: Optional[str] = None
    ) -> "DrillholeDatabase":
        """
        Create a DrillholeDatabase instance linked to an existing database.
        
        This method keeps a persistent connection to the database and loads
        data on-demand rather than loading everything into memory.
        
        Parameters
        ----------
        db_path : str
            Path to the SQLite database file
        project_name : str, optional
            Name of the project to link to. If None, links to all data.
        
        Returns
        -------
        DrillholeDatabase
            Database instance linked to file
        """
        return cls.from_database(db_path, project_name)
    
    def save_to_database(
        self,
        db_path: str,
        project_name: Optional[str] = None,
        overwrite: bool = False
    ):
        """
        Save the current database to a SQLite file.
        
        Parameters
        ----------
        db_path : str
            Path to the SQLite database file
        project_name : str, optional
            Name of the project to save as
        overwrite : bool, optional
            If True, overwrite existing data for this project
        """
        db_config = DbConfig(backend='file', db_path=db_path, project_name=project_name)
        
        # Create connection
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Create tables
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS projects (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT UNIQUE NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                metadata TEXT
            )
        ''')
        
        # Handle project
        project_id = None
        if project_name:
            if overwrite:
                # Delete existing project data
                cursor.execute('SELECT id FROM projects WHERE name = ?', (project_name,))
                result = cursor.fetchone()
                if result:
                    project_id = result[0]
                    cursor.execute('DELETE FROM collar WHERE project_id = ?', (project_id,))
                    cursor.execute('DELETE FROM survey WHERE project_id = ?', (project_id,))
                else:
                    cursor.execute('INSERT INTO projects (name) VALUES (?)', (project_name,))
                    project_id = cursor.lastrowid
            else:
                cursor.execute('INSERT OR IGNORE INTO projects (name) VALUES (?)', (project_name,))
                cursor.execute('SELECT id FROM projects WHERE name = ?', (project_name,))
                project_id = cursor.fetchone()[0]
        
        # Save collar and survey
        collar_data = self.collar.copy()
        survey_data = self.survey.copy()
        
        if project_id:
            collar_data['project_id'] = project_id
            survey_data['project_id'] = project_id
        
        collar_data.to_sql('collar', conn, if_exists='append', index=False)
        survey_data.to_sql('survey', conn, if_exists='append', index=False)
        
        # Save interval and point tables
        for name, df in self.intervals.items():
            table_data = df.copy()
            if project_id:
                table_data['project_id'] = project_id
            table_data.to_sql(f'interval_{name}', conn, if_exists='append', index=False)
        
        for name, df in self.points.items():
            table_data = df.copy()
            if project_id:
                table_data['project_id'] = project_id
            table_data.to_sql(f'point_{name}', conn, if_exists='append', index=False)
        
        conn.commit()
        conn.close()
    
    def __del__(self):
        """Clean up database connection."""
        if hasattr(self, '_conn') and self._conn is not None:
            try:
                self._conn.close()
            except:
                pass

    @classmethod
    def from_csv(
        cls,
        collar_file: str,
        survey_file: str,
        collar_columns: Optional[Dict[str, str]] = None,
        survey_columns: Optional[Dict[str, str]] = None,
        **kwargs
    ) -> "DrillholeDatabase":
        """
        Create a DrillholeDatabase from CSV files with column mapping.

        Parameters
        ----------
        collar_file : str
            Path to the collar CSV file
        survey_file : str
            Path to the survey CSV file
        collar_columns : dict, optional
            Mapping of CSV column names to required DrillholeDatabase columns.
            Keys should be DhConfig field names (holeid, x, y, z, total_depth).
            Values should be the actual column names in the CSV file.
            Example: {
                'holeid': 'HOLE_ID',
                'x': 'X_MGA',
                'y': 'Y_MGA',
                'z': 'Z_MGA',
                'total_depth': 'DEPTH'
            }
        survey_columns : dict, optional
            Mapping of CSV column names to required DrillholeDatabase columns.
            Keys should be DhConfig field names (holeid, depth, azimuth, dip).
            Values should be the actual column names in the CSV file.
            Example: {
                'holeid': 'Drillhole ID',
                'depth': 'Depth',
                'azimuth': 'Azimuth',
                'dip': 'Dip'
            }
        **kwargs
            Additional keyword arguments passed to pd.read_csv()

        Returns
        -------
        DrillholeDatabase
            New DrillholeDatabase instance with data loaded from CSV files

        Examples
        --------
        Load CSV files with column mapping:

        >>> db = DrillholeDatabase.from_csv(
        ...     collar_file='collar.csv',
        ...     survey_file='survey.csv',
        ...     collar_columns={
        ...         'holeid': 'HOLE_ID',
        ...         'x': 'X_MGA',
        ...         'y': 'Y_MGA',
        ...         'z': 'Z_MGA',
        ...         'total_depth': 'DEPTH'
        ...     },
        ...     survey_columns={
        ...         'holeid': 'Drillhole ID',
        ...         'depth': 'Depth',
        ...         'azimuth': 'Azimuth',
        ...         'dip': 'Dip'
        ...     }
        ... )

        Load CSV files without mapping (assumes columns match DhConfig names):

        >>> db = DrillholeDatabase.from_csv(
        ...     collar_file='collar.csv',
        ...     survey_file='survey.csv'
        ... )
        """
        # Read CSV files
        collar_raw = pd.read_csv(collar_file, **kwargs)
        survey_raw = pd.read_csv(survey_file, **kwargs)

        # Map collar columns
        if collar_columns is not None:
            # Create mapping from config field names to actual column names
            collar_df = pd.DataFrame()
            for config_field, csv_column in collar_columns.items():
                # Get the actual DhConfig attribute value
                config_col_name = getattr(DhConfig, config_field, config_field)
                if csv_column not in collar_raw.columns:
                    raise ValueError(
                        f"Column '{csv_column}' specified in collar_columns mapping not found in collar CSV. "
                        f"Available columns: {list(collar_raw.columns)}"
                    )
                collar_df[config_col_name] = collar_raw[csv_column]
            
            # Add any remaining columns that weren't mapped
            for col in collar_raw.columns:
                if col not in collar_columns.values():
                    collar_df[col] = collar_raw[col]
        else:
            collar_df = collar_raw.copy()

        # Map survey columns
        if survey_columns is not None:
            # Create mapping from config field names to actual column names
            survey_df = pd.DataFrame()
            for config_field, csv_column in survey_columns.items():
                # Get the actual DhConfig attribute value
                config_col_name = getattr(DhConfig, config_field, config_field)
                if csv_column not in survey_raw.columns:
                    raise ValueError(
                        f"Column '{csv_column}' specified in survey_columns mapping not found in survey CSV. "
                        f"Available columns: {list(survey_raw.columns)}"
                    )
                survey_df[config_col_name] = survey_raw[csv_column]
            
            # Add any remaining columns that weren't mapped
            for col in survey_raw.columns:
                if col not in survey_columns.values():
                    survey_df[col] = survey_raw[col]
        else:
            survey_df = survey_raw.copy()

        # Remove rows with missing essential data
        required_collar_cols = [DhConfig.holeid, DhConfig.x, DhConfig.y, DhConfig.z, DhConfig.total_depth]
        collar_df = collar_df.dropna(subset=required_collar_cols)

        required_survey_cols = [DhConfig.holeid, DhConfig.depth, DhConfig.azimuth, DhConfig.dip]
        survey_df = survey_df.dropna(subset=required_survey_cols)

        # Create and return DrillholeDatabase instance
        return cls(collar=collar_df, survey=survey_df)

    def _validate_collar(self):
        """Validate collar DataFrame structure."""
        required_cols = [DhConfig.holeid, DhConfig.x, DhConfig.y, DhConfig.z, DhConfig.total_depth]
        missing_cols = [col for col in required_cols if col not in self.collar.columns]
        if missing_cols:
            raise ValueError(f"Missing required collar columns: {missing_cols}")

        if self.collar[DhConfig.holeid].duplicated().any():
            raise ValueError("Duplicate HOLE_IDs found in collar data")

    def _validate_survey(self):
        """Validate survey DataFrame structure."""
        required_cols = [DhConfig.holeid, DhConfig.depth, DhConfig.azimuth, DhConfig.dip]
        missing_cols = [col for col in required_cols if col not in self.survey.columns]
        if missing_cols:
            raise ValueError(f"Missing required survey columns: {missing_cols}")

        # Check that all survey holes exist in collar
        survey_holes = set(self.survey[DhConfig.holeid])
        collar_holes = set(self.collar[DhConfig.holeid])
        missing_holes = survey_holes - collar_holes
        if missing_holes:
            raise ValueError(f"Survey holes not found in collar: {missing_holes}")

    def _normalize_angles(self):
        """Convert angles to radians if they appear to be in degrees."""
        # Check azimuth range
        az_range = self.survey[DhConfig.azimuth].max() - self.survey[DhConfig.azimuth].min()
        if az_range > 2 * np.pi:
            logger.info("Converting azimuth from degrees to radians")
            self.survey[DhConfig.azimuth] = np.deg2rad(self.survey[DhConfig.azimuth])

        # Check dip range
        dip_range = self.survey[DhConfig.dip].max() - self.survey[DhConfig.dip].min()
        if dip_range > np.pi:
            logger.info("Converting dip from degrees to radians")
            self.survey[DhConfig.dip] = np.deg2rad(self.survey[DhConfig.dip])

    def __getitem__(self, hole_id: str) -> DrillHole:
        """
        Return a DrillHole view for a given HOLE_ID.

        Parameters
        ----------
        hole_id : str
            The hole identifier

        Returns
        -------
        DrillHole
            A view of this database for the specified hole
        """
        return DrillHole(self, hole_id)

    def add_interval_table(self, name: str, df: pd.DataFrame):
        """
        Register a new interval table.

        Parameters
        ----------
        name : str
            Unique name for the table
        df : pd.DataFrame
            Interval data with required columns: HOLE_ID, FROM, TO
        """
        df = df.copy()

        # Validate required columns
        required_cols = [DhConfig.holeid, DhConfig.sample_from, DhConfig.sample_to]
        missing_cols = [col for col in required_cols if col not in df.columns]
        if missing_cols:
            raise ValueError(f"Missing required interval columns: {missing_cols}")

        # Validate holes exist in collar
        interval_holes = set(df[DhConfig.holeid])
        collar_holes = set(self.collar[DhConfig.holeid])
        missing_holes = interval_holes - collar_holes
        if missing_holes:
            raise ValueError(f"Interval holes not found in collar: {missing_holes}")

        self.intervals[name] = df

    def add_point_table(self, name: str, df: pd.DataFrame):
        """
        Register a new point table.

        Parameters
        ----------
        name : str
            Unique name for the table
        df : pd.DataFrame
            Point data with required columns: HOLE_ID, DEPTH
        """
        df = df.copy()

        # Validate required columns
        required_cols = [DhConfig.holeid, DhConfig.depth]
        missing_cols = [col for col in required_cols if col not in df.columns]
        if missing_cols:
            raise ValueError(f"Missing required point columns: {missing_cols}")

        # Validate holes exist in collar
        point_holes = set(df[DhConfig.holeid])
        collar_holes = set(self.collar[DhConfig.holeid])
        missing_holes = point_holes - collar_holes
        if missing_holes:
            raise ValueError(f"Point holes not found in collar: {missing_holes}")

        self.points[name] = df

    def list_holes(self) -> List[str]:
        """Return all HOLE_IDs."""
        return sorted(self.collar[DhConfig.holeid].tolist())

    def extent(self) -> Tuple[float, float, float, float, float, float]:
        """
        Return spatial extent of all drillholes.

        Returns
        -------
        tuple
            (xmin, xmax, ymin, ymax, zmin, zmax)
        """
        x_col, y_col, z_col = DhConfig.x, DhConfig.y, DhConfig.z

        xmin, xmax = self.collar[x_col].min(), self.collar[x_col].max()
        ymin, ymax = self.collar[y_col].min(), self.collar[y_col].max()
        zmin, zmax = self.collar[z_col].min(), self.collar[z_col].max()

        return (xmin, xmax, ymin, ymax, zmin, zmax)

    def filter(
        self,
        holes: Optional[List[str]] = None,
        bbox: Optional[Tuple[float, float, float, float]] = None,
        depth_range: Optional[Tuple[float, float]] = None,
        expr: Optional[Union[str, Callable]] = None,
    ) -> "DrillholeDatabase":
        """
        Return a filtered DrillholeDatabase.

        Parameters
        ----------
        holes : list[str], optional
            List of HOLE_IDs to keep
        bbox : tuple, optional
            (xmin, xmax, ymin, ymax) filter by collar XY
        depth_range : tuple, optional
            (min_depth, max_depth) clip survey/interval/point data
        expr : str or callable, optional
            Pandas query string or callable applied to intervals/points

        Returns
        -------
        DrillholeDatabase
            New filtered database instance
        """
        # Start with all collar data
        collar_mask = pd.Series(True, index=self.collar.index)

        # Apply holes filter
        if holes is not None:
            collar_mask &= self.collar[DhConfig.holeid].isin(holes)

        # Apply bounding box filter
        if bbox is not None:
            xmin, xmax, ymin, ymax = bbox
            collar_mask &= (
                (self.collar[DhConfig.x] >= xmin)
                & (self.collar[DhConfig.x] <= xmax)
                & (self.collar[DhConfig.y] >= ymin)
                & (self.collar[DhConfig.y] <= ymax)
            )

        # Filter collar
        filtered_collar = self.collar[collar_mask].copy()
        filtered_hole_ids = set(filtered_collar[DhConfig.holeid])

        # Filter survey
        survey_mask = self.survey[DhConfig.holeid].isin(filtered_hole_ids)
        filtered_survey = self.survey[survey_mask].copy()

        # Apply depth range to survey
        if depth_range is not None:
            min_depth, max_depth = depth_range
            depth_mask = (filtered_survey[DhConfig.depth] >= min_depth) & (
                filtered_survey[DhConfig.depth] <= max_depth
            )
            filtered_survey = filtered_survey[depth_mask].copy()

        # Create new database instance
        new_db = DrillholeDatabase(filtered_collar, filtered_survey)

        # Filter interval tables
        for name, table in self.intervals.items():
            # Filter by holes
            table_mask = table[DhConfig.holeid].isin(filtered_hole_ids)
            filtered_table = table[table_mask].copy()

            # Apply depth range
            if depth_range is not None and not filtered_table.empty:
                min_depth, max_depth = depth_range
                depth_mask = (filtered_table[DhConfig.sample_from] <= max_depth) & (
                    filtered_table[DhConfig.sample_to] >= min_depth
                )
                filtered_table = filtered_table[depth_mask].copy()

                # Clip interval boundaries
                filtered_table[DhConfig.sample_from] = filtered_table[DhConfig.sample_from].clip(
                    lower=min_depth
                )
                filtered_table[DhConfig.sample_to] = filtered_table[DhConfig.sample_to].clip(
                    upper=max_depth
                )

            # Apply expression filter
            if expr is not None and not filtered_table.empty:
                try:
                    if callable(expr):
                        filtered_table = filtered_table[expr(filtered_table)].copy()
                    elif isinstance(expr, str):
                        filtered_table = filtered_table.query(expr).copy()
                except (KeyError, pd.errors.UndefinedVariableError):
                    # Expression doesn't apply to this table (e.g., LITHO column not present)
                    pass

            if not filtered_table.empty:
                new_db.intervals[name] = filtered_table

        # Filter point tables
        for name, table in self.points.items():
            # Filter by holes
            table_mask = table[DhConfig.holeid].isin(filtered_hole_ids)
            filtered_table = table[table_mask].copy()

            # Apply depth range
            if depth_range is not None and not filtered_table.empty:
                min_depth, max_depth = depth_range
                depth_mask = (filtered_table[DhConfig.depth] >= min_depth) & (
                    filtered_table[DhConfig.depth] <= max_depth
                )
                filtered_table = filtered_table[depth_mask].copy()

            # Apply expression filter
            if expr is not None and not filtered_table.empty:
                try:
                    if callable(expr):
                        filtered_table = filtered_table[expr(filtered_table)].copy()
                    elif isinstance(expr, str):
                        filtered_table = filtered_table.query(expr).copy()
                except (KeyError, pd.errors.UndefinedVariableError):
                    # Expression doesn't apply to this table (e.g., column not present)
                    pass

            if not filtered_table.empty:
                new_db.points[name] = filtered_table

        return new_db

    def validate(self) -> bool:
        """
        Perform schema and consistency checks.

        Returns
        -------
        bool
            True if all validations pass

        Raises
        ------
        ValueError
            If validation fails
        """
        # Check collar and survey (already done in __init__)
        self._validate_collar()
        self._validate_survey()

        # Validate interval tables
        for name, table in self.intervals.items():
            # Check holes exist
            interval_holes = set(table[DhConfig.holeid])
            collar_holes = set(self.collar[DhConfig.holeid])
            missing_holes = interval_holes - collar_holes
            if missing_holes:
                raise ValueError(
                    f"Interval table '{name}' has holes not in collar: {missing_holes}"
                )

            # Check depths don't exceed total depth
            for hole_id in interval_holes:
                collar_row = self.collar[self.collar[DhConfig.holeid] == hole_id].iloc[0]
                total_depth = collar_row[DhConfig.total_depth]

                hole_intervals = table[table[DhConfig.holeid] == hole_id]
                max_to = hole_intervals[DhConfig.sample_to].max()

                if max_to > total_depth:
                    raise ValueError(
                        f"Interval in table '{name}' for hole '{hole_id}' exceeds total depth"
                    )

        # Validate point tables
        for name, table in self.points.items():
            # Check holes exist
            point_holes = set(table[DhConfig.holeid])
            collar_holes = set(self.collar[DhConfig.holeid])
            missing_holes = point_holes - collar_holes
            if missing_holes:
                raise ValueError(f"Point table '{name}' has holes not in collar: {missing_holes}")

            # Check depths don't exceed total depth
            for hole_id in point_holes:
                collar_row = self.collar[self.collar[DhConfig.holeid] == hole_id].iloc[0]
                total_depth = collar_row[DhConfig.total_depth]

                hole_points = table[table[DhConfig.holeid] == hole_id]
                max_depth = hole_points[DhConfig.depth].max()

                if max_depth > total_depth:
                    raise ValueError(
                        f"Point in table '{name}' for hole '{hole_id}' exceeds total depth"
                    )

        return True

    def vtk(
        self, 
        newinterval: Union[float, np.ndarray] = 1.0, 
        radius: float = 0.1,
        properties: Optional[List[str]] = None
    ):
        """
        Return a PyVista MultiBlock object containing all drillholes as tubes.

        Parameters
        ----------
        newinterval : float or array-like, default 1.0
            Step size for interpolation along hole depth, or specific depths to sample
        radius : float, default 0.1
            Radius of the tube representation for each drillhole
        properties : list of str, optional
            List of property names (interval table names) to attach as cell data.
            Properties will be resampled to match the trace intervals.

        Returns
        -------
        pyvista.MultiBlock
            PyVista MultiBlock object containing all drillhole tubes with optional cell properties

        Examples
        --------
        >>> # Create VTK with lithology as cell property
        >>> multiblock = db.vtk(newinterval=1.0, properties=['lithology'])
        """
        try:
            import pyvista as pv
        except ImportError:
            raise ImportError(
                "PyVista is required for VTK output. Install with: pip install pyvista"
            )

        # Create MultiBlock dataset
        multiblock = pv.MultiBlock()

        # Add each drillhole as a tube to the multiblock
        for hole_id in self.list_holes():
            try:
                drillhole = self[hole_id]
                tube = drillhole.vtk(newinterval=newinterval, radius=radius, properties=properties)
                multiblock[hole_id] = tube
            except Exception as e:
                logger.warning(f"Failed to create VTK tube for hole {hole_id}: {e}")
                continue

        return multiblock

    def desurvey_intervals(self, interval_table_name: str) -> pd.DataFrame:
        """
        Desurvey interval data for all holes to get 3D coordinates.

        Parameters
        ----------
        interval_table_name : str
            Name of the interval table to desurvey

        Returns
        -------
        pd.DataFrame
            Combined interval data from all holes with added 3D coordinate columns
        """
        if interval_table_name not in self.intervals:
            raise KeyError(f"Interval table '{interval_table_name}' not found")

        desurveyed_intervals = []

        # Process each hole
        for hole_id in self.list_holes():
            try:
                drillhole = self[hole_id]
                hole_intervals = drillhole.desurvey_intervals(interval_table_name)
                if not hole_intervals.empty:
                    desurveyed_intervals.append(hole_intervals)
            except Exception as e:
                logger.warning(f"Failed to desurvey intervals for hole {hole_id}: {e}")
                continue

        if not desurveyed_intervals:
            # Return empty DataFrame with expected structure
            return pd.DataFrame(
                columns=[
                    DhConfig.holeid,
                    DhConfig.sample_from,
                    DhConfig.sample_to,
                    "x_from",
                    "y_from",
                    "z_from",
                    "x_to",
                    "y_to",
                    "z_to",
                    "x_mid",
                    "y_mid",
                    "z_mid",
                    "depth_mid",
                ]
            )

        return pd.concat(desurveyed_intervals, ignore_index=True)

    def desurvey_points(self, point_table_name: str) -> pd.DataFrame:
        """
        Desurvey point data for all holes to get 3D coordinates.

        Parameters
        ----------
        point_table_name : str
            Name of the point table to desurvey

        Returns
        -------
        pd.DataFrame
            Combined point data from all holes with added 3D coordinate columns
        """
        if point_table_name not in self.points:
            raise KeyError(f"Point table '{point_table_name}' not found")

        desurveyed_points = []

        # Process each hole
        for hole_id in self.list_holes():
            try:
                drillhole = self[hole_id]
                hole_points = drillhole.desurvey_points(point_table_name)
                if not hole_points.empty:
                    desurveyed_points.append(hole_points)
            except Exception as e:
                logger.warning(f"Failed to desurvey points for hole {hole_id}: {e}")
                continue

        if not desurveyed_points:
            # Return empty DataFrame with expected structure
            return pd.DataFrame(columns=[DhConfig.holeid, DhConfig.depth, "x", "y", "z"])

        return pd.concat(desurveyed_points, ignore_index=True)
