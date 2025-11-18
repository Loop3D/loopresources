"""DrillHoleDatabase - A clean implementation based on AGENTS.md specifications.

This module provides a modern, pandas-native interface for drillhole data management
with filtering, validation, and export capabilities.
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Tuple, Union, Callable
import logging
import sqlite3
from pathlib import Path
from LoopStructural.utils import (
    normal_vector_to_strike_and_dip,
)  # , normal_vector_to_dip_and_dip_direction
from LoopStructural import BoundingBox

from .dhconfig import DhConfig
from .dbconfig import DbConfig
from .drillhole import DrillHole
from .orientation import alphaBeta2vector

logger = logging.getLogger(__name__)


class DrillholeDatabase:
    """Main container for all drillhole data.

    Stores global data as pandas DataFrames and dictionaries following
    the specification in AGENTS.md.
    """

    def __init__(
        self, collar: pd.DataFrame, survey: pd.DataFrame, db_config: Optional[DbConfig] = None
    ):
        """Initialize DrillholeDatabase.

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
        self.db_config = db_config if db_config is not None else DbConfig(backend="memory")
        self._conn = None

        # Store data based on backend configuration
        if self.db_config.backend == "memory":
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
        if self.db_config.backend == "memory":
            return (
                self._collar
                if hasattr(self, "_collar") and self._collar is not None
                else getattr(self, "_memory_collar", pd.DataFrame())
            )
        else:
            return self._load_table_from_db("collar")

    @collar.setter
    def collar(self, value: pd.DataFrame):
        """Set collar data."""
        if self.db_config.backend == "memory":
            self._memory_collar = value
        else:
            self._collar = value

    @property
    def survey(self) -> pd.DataFrame:
        """Get survey data from memory or database."""
        if self.db_config.backend == "memory":
            return (
                self._survey
                if hasattr(self, "_survey") and self._survey is not None
                else getattr(self, "_memory_survey", pd.DataFrame())
            )
        else:
            return self._load_table_from_db("survey")

    @survey.setter
    def survey(self, value: pd.DataFrame):
        """Set survey data."""
        if self.db_config.backend == "memory":
            self._memory_survey = value
        else:
            self._survey = value

    def plot_collars(self, ax=None, **kwargs):
        """Plot collar locations.

        Parameters
        ----------
        ax : matplotlib.axes.Axes, optional
            Matplotlib Axes to plot on. If None, creates a new figure and axes.
        **kwargs
            Additional keyword arguments passed to ax.scatter()

        Returns
        -------
        matplotlib.axes.Axes
            The Axes object with the plot
        """
        import matplotlib.pyplot as plt

        if ax is None:
            fig, ax = plt.subplots(figsize=(8, 6))

        collar = self.collar
        ax.scatter(collar[DhConfig.x], collar[DhConfig.y], **kwargs)
        ax.set_xlabel("X")
        ax.set_ylabel("Y")
        ax.set_title("Collar Locations")
        ax.axis("equal")
        for x, y, hole_id in zip(collar[DhConfig.x], collar[DhConfig.y], collar[DhConfig.holeid]):
            ax.text(x, y, hole_id, fontsize=9, ha="right", va="bottom")
        return ax

    def get_collar_for_hole(self, hole_id: str) -> pd.DataFrame:
        """Get collar data for a specific hole.

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
        if self.db_config.backend == "memory":
            collar_data = self.collar
            mask = collar_data[DhConfig.holeid] == hole_id
            return collar_data[mask].copy()
        else:
            return self._load_table_from_db("collar", hole_id=hole_id)

    def get_survey_for_hole(self, hole_id: str) -> pd.DataFrame:
        """Get survey data for a specific hole.

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
        if self.db_config.backend == "memory":
            survey_data = self.survey
            mask = survey_data[DhConfig.holeid] == hole_id
            return survey_data[mask].copy()
        else:
            return self._load_table_from_db("survey", hole_id=hole_id)

    def get_interval_data_for_hole(self, table_name: str, hole_id: str) -> pd.DataFrame:
        """Get interval table data for a specific hole.

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
        """Get point table data for a specific hole.

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
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS projects (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT UNIQUE NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                metadata TEXT
            )
        """
        )

        # Insert project if specified
        if self.db_config.project_name:
            cursor.execute(
                "INSERT OR IGNORE INTO projects (name) VALUES (?)", (self.db_config.project_name,)
            )

        self._conn.commit()

    def _get_project_id(self) -> Optional[int]:
        """Get project ID from database."""
        if not self.db_config.project_name:
            return None

        cursor = self._conn.cursor()
        cursor.execute("SELECT id FROM projects WHERE name = ?", (self.db_config.project_name,))
        result = cursor.fetchone()
        return result[0] if result else None

    def _store_data_to_db(self, collar: pd.DataFrame, survey: pd.DataFrame):
        """Store collar and survey data to database."""
        project_id = self._get_project_id()

        # Add project_id column if project is specified
        if project_id is not None:
            collar = collar.copy()
            collar["project_id"] = project_id
            survey = survey.copy()
            survey["project_id"] = project_id

        # Store to SQLite
        collar.to_sql("collar", self._conn, if_exists="append", index=False)
        survey.to_sql("survey", self._conn, if_exists="append", index=False)

    def _load_table_from_db(self, table_name: str, hole_id: Optional[str] = None) -> pd.DataFrame:
        """Load table from database.

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
        if "project_id" in df.columns:
            df = df.drop(columns=["project_id"])

        return df

    @classmethod
    def from_database(cls, db_path: str, project_name: Optional[str] = None) -> "DrillholeDatabase":
        """Load DrillholeDatabase from an existing SQLite database.

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
        db_config = DbConfig(backend="file", db_path=db_path, project_name=project_name)

        # Connect to database and load collar/survey
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # Check if projects table exists
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='projects'")
        projects_table_exists = cursor.fetchone() is not None

        # Load collar and survey
        if project_name:
            if not projects_table_exists:
                conn.close()
                raise ValueError("Projects table not found in database")

            # Get project_id
            cursor.execute("SELECT id FROM projects WHERE name = ?", (project_name,))
            result = cursor.fetchone()
            if result is None:
                conn.close()
                raise ValueError(f"Project '{project_name}' not found in database")
            project_id = result[0]

            collar = pd.read_sql_query(
                "SELECT * FROM collar WHERE project_id = ?", conn, params=(project_id,)
            )
            survey = pd.read_sql_query(
                "SELECT * FROM survey WHERE project_id = ?", conn, params=(project_id,)
            )

            # Remove project_id from dataframes
            if "project_id" in collar.columns:
                collar = collar.drop(columns=["project_id"])
            if "project_id" in survey.columns:
                survey = survey.drop(columns=["project_id"])
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
        cls, db_path: str, project_name: Optional[str] = None
    ) -> "DrillholeDatabase":
        """Create a DrillholeDatabase instance linked to an existing database.

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
        self, db_path: str, project_name: Optional[str] = None, overwrite: bool = False
    ):
        """Save the current database to a SQLite file.

        Parameters
        ----------
        db_path : str
            Path to the SQLite database file
        project_name : str, optional
            Name of the project to save as
        overwrite : bool, optional
            If True, overwrite existing data for this project
        """
        db_config = DbConfig(backend="file", db_path=db_path, project_name=project_name)

        # Create connection
        conn = sqlite3.connect(db_config.db_path)
        cursor = conn.cursor()

        # Create tables
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS projects (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT UNIQUE NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                metadata TEXT
            )
        """
        )

        # Handle project
        project_id = None
        if project_name:
            if overwrite:
                # Delete existing project data
                cursor.execute("SELECT id FROM projects WHERE name = ?", (project_name,))
                result = cursor.fetchone()
                if result:
                    project_id = result[0]
                    cursor.execute("DELETE FROM collar WHERE project_id = ?", (project_id,))
                    cursor.execute("DELETE FROM survey WHERE project_id = ?", (project_id,))
                else:
                    cursor.execute("INSERT INTO projects (name) VALUES (?)", (project_name,))
                    project_id = cursor.lastrowid
            else:
                cursor.execute("INSERT OR IGNORE INTO projects (name) VALUES (?)", (project_name,))
                cursor.execute("SELECT id FROM projects WHERE name = ?", (project_name,))
                project_id = cursor.fetchone()[0]

        # Save collar and survey
        collar_data = self.collar.copy()
        survey_data = self.survey.copy()

        if project_id:
            collar_data["project_id"] = project_id
            survey_data["project_id"] = project_id

        collar_data.to_sql("collar", conn, if_exists="append", index=False)
        survey_data.to_sql("survey", conn, if_exists="append", index=False)

        # Save interval and point tables
        for name, df in self.intervals.items():
            table_data = df.copy()
            if project_id:
                table_data["project_id"] = project_id
            table_data.to_sql(f"interval_{name}", conn, if_exists="append", index=False)

        for name, df in self.points.items():
            table_data = df.copy()
            if project_id:
                table_data["project_id"] = project_id
            table_data.to_sql(f"point_{name}", conn, if_exists="append", index=False)

        conn.commit()
        conn.close()

    def __del__(self):
        """Clean up database connection."""
        if hasattr(self, "_conn") and self._conn is not None:
            try:
                self._conn.close()
            except:
                pass

    @classmethod
    def from_csv(
        cls,
        collar_file: str,
        survey_file: str,
        collar_columns: Dict[str, str] = {},
        survey_columns: Dict[str, str] = {},
        **kwargs,
    ) -> "DrillholeDatabase":
        """Create a DrillholeDatabase from CSV files with column mapping.

        Parameters
        ----------
        collar_file : str
            Path to the collar CSV file
        survey_file : str
            Path to the survey CSV file
        collar_columns : dict, optional
            Mapping of CSV column names to required DrillholeDatabase columns.
            Uses pandas.rename semantics.
            Keys should be the actual column names in the CSV file.
            Values should be DhConfig field names (holeid, x, y, z, total_depth).
            Example: {
                'HOLE_ID': DhConfig.holeid,
                'X_MGA': DhConfig.x,
                'Y_MGA': DhConfig.y,
                'Z_MGA': DhConfig.z,
                'DEPTH': DhConfig.total_depth   
            }
        survey_columns : dict, optional
            Mapping of CSV column names to required DrillholeDatabase columns.
            Keys should be actual column names
            Values should be DhConfig field names (holeid, depth, azimuth, dip).
            Values should be the actual column names in the CSV file.
            Example: {
                'Drillhole ID': DhConfig.holeid,
                'Depth': DhConfig.depth,
                'Azimuth': DhConfig.azimuth,
                'Dip': DhConfig.dip 
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
        ...         'HOLE_ID': DhConfig.holeid,
        ...         'X_MGA': DhConfig.x,
        ...         'Y_MGA': DhConfig.y,
        ...         'Z_MGA': DhConfig.z,
        ...         'DEPTH': DhConfig.total_depth
        ...     },
        ...     survey_columns={
        ...         'Drillhole ID': DhConfig.holeid,
        ...         'Depth': DhConfig.depth,
        ...         'Azimuth': DhConfig.azimuth,
        ...         'Dip': DhConfig.dip
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
        collar_df = collar_raw.rename(columns=collar_columns)
        survey_df = survey_raw.rename(columns=survey_columns)

        # Remove rows with missing essential data
        required_collar_cols = [
            DhConfig.holeid,
            DhConfig.x,
            DhConfig.y,
            DhConfig.z,
            DhConfig.total_depth,
        ]
        for col in required_collar_cols:
            if col not in collar_df.columns:
                raise KeyError(f"Required collar column '{col}' not found in CSV file")
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
        if DhConfig.positive_dips_down:
            self.survey.loc[self.survey[DhConfig.dip] > 0, DhConfig.dip] = -self.survey.loc[
                self.survey[DhConfig.dip] > 0, DhConfig.dip
            ]
    def _normalize_angles(self):
        """Convert angles to radians if they appear to be in degrees."""
        # Work on a copy of the survey DataFrame and write back via the property
        # setter to avoid chained-assignment warnings and to ensure the
        # underlying storage (memory or file-backed) is updated correctly.
        survey_df = self.survey.copy()

        # Check azimuth range safely (handle empty/NaN cases)
        az_min = survey_df[DhConfig.azimuth].min()
        az_max = survey_df[DhConfig.azimuth].max()
        az_range = (az_max - az_min) if pd.notna(az_min) and pd.notna(az_max) else 0.0
        if az_range > 2 * np.pi:
            logger.info("Converting azimuth from degrees to radians")
            survey_df[DhConfig.azimuth] = np.deg2rad(survey_df[DhConfig.azimuth])

        # Check dip range safely (handle empty/NaN cases)
        dip_min = survey_df[DhConfig.dip].min()
        dip_max = survey_df[DhConfig.dip].max()
        dip_range = (dip_max - dip_min) if pd.notna(dip_min) and pd.notna(dip_max) else 0.0
        if dip_range > np.pi:
            logger.info("Converting dip from degrees to radians")
            survey_df[DhConfig.dip] = np.deg2rad(survey_df[DhConfig.dip])

        # Assign the modified DataFrame back through the property setter so the
        # underlying attribute is updated in a single operation (no chained assignment).
        self.survey = survey_df

    def __getitem__(self, hole_id: str) -> DrillHole:
        """Return a DrillHole view for a given HOLE_ID.

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

    def __iter__(self):
        """Iterate over all DrillHole objects in the database.

        Yields
        ------
        DrillHole
            A view of this database for each hole

        Examples
        --------
        >>> for drillhole in database:
        ...     print(drillhole.hole_id)
        """
        for hole_id in self.list_holes():
            yield self[hole_id]

    def __repr__(self) -> str:
        """Return a concise representation of the DrillholeDatabase."""
        num_holes = len(self.list_holes())
        num_intervals = len(self.intervals)
        num_points = len(self.points)
        return f"DrillholeDatabase(holes={num_holes}, interval_tables={num_intervals}, point_tables={num_points})"

    def __str__(self) -> str:
        """Return a detailed string representation of the DrillholeDatabase."""
        num_holes = len(self.list_holes())

        # Get spatial extent
        bb = self.extent()
        xmin, ymin, zmin = bb.global_origin[:3]
        xmax, ymax, zmax = bb.global_maximum[:3]
        lines = [
            "DrillholeDatabase",
            "=================",
            f"Number of Drillholes: {num_holes}",
            "Spatial Extent:",
            f"  X: {xmin:.2f} to {xmax:.2f} (range: {xmax - xmin:.2f})",
            f"  Y: {ymin:.2f} to {ymax:.2f} (range: {ymax - ymin:.2f})",
            f"  Z: {zmin:.2f} to {zmax:.2f} (range: {zmax - zmin:.2f})",
        ]

        # Add interval tables information
        if self.intervals:
            lines.append(f"\nInterval Tables ({len(self.intervals)}):")
            for table_name, table_df in self.intervals.items():
                num_rows = len(table_df)
                # Get columns excluding standard ones
                data_cols = [
                    col
                    for col in table_df.columns
                    if col
                    not in [
                        DhConfig.holeid,
                        DhConfig.sample_from,
                        DhConfig.sample_to,
                        DhConfig.depth,
                    ]
                ]

                lines.append(f"  - {table_name}:")
                lines.append(f"    Rows: {num_rows}")
                if data_cols:
                    lines.append(f"    Columns: {', '.join(data_cols)}")
                else:
                    lines.append("    Columns: (none)")

                # Count how many holes have data in this table
                holes_with_data = table_df[DhConfig.holeid].nunique()
                lines.append(f"    Holes with data: {holes_with_data}/{num_holes}")
        else:
            lines.append("\nInterval Tables: None")

        # Add point tables information
        if self.points:
            lines.append(f"\nPoint Tables ({len(self.points)}):")
            for table_name, table_df in self.points.items():
                num_rows = len(table_df)
                # Get columns excluding standard ones
                data_cols = [
                    col for col in table_df.columns if col not in [DhConfig.holeid, DhConfig.depth]
                ]

                lines.append(f"  - {table_name}:")
                lines.append(f"    Rows: {num_rows}")
                if data_cols:
                    lines.append(f"    Columns: {', '.join(data_cols)}")
                else:
                    lines.append("    Columns: (none)")

                # Count how many holes have data in this table
                holes_with_data = table_df[DhConfig.holeid].nunique()
                lines.append(f"    Holes with data: {holes_with_data}/{num_holes}")
        else:
            lines.append("\nPoint Tables: None")

        return "\n".join(lines)

    def sorted_by(
        self, key: Optional[Union[str, Callable[[DrillHole], float]]] = None, reverse: bool = False
    ):
        """Iterate over DrillHole objects in sorted order.

        Parameters
        ----------
        key : str or callable, optional
            Sorting key. Can be:
            - A string: column name from collar table (e.g., 'EAST', 'NORTH', 'DEPTH')
            - A callable: function that takes a DrillHole and returns a sortable value
            - None: sort by hole_id (default)
        reverse : bool, default False
            If True, sort in descending order

        Yields
        ------
        DrillHole
            A view of this database for each hole, in sorted order

        Examples
        --------
        Sort by collar column:

        >>> for h in db.sorted_by('DEPTH', reverse=True):
        ...     print(f"{h.hole_id}: {h.collar['DEPTH'].iloc[0]}m")

        Sort by maximum assay value:

        >>> def max_cu(hole):
        ...     assay = hole['assay']
        ...     return assay['CU_PPM'].max() if not assay.empty else 0
        >>> for h in db.sorted_by(max_cu, reverse=True):
        ...     print(f"{h.hole_id}: max Cu = {max_cu(h)}")

        Sort by meters where assay exceeds threshold:

        >>> def high_grade_meters(hole):
        ...     assay = hole['assay']
        ...     if assay.empty:
        ...         return 0
        ...     high_grade = assay[assay['CU_PPM'] > 1000]
        ...     return (high_grade[DhConfig.sample_to] - high_grade[DhConfig.sample_from]).sum()
        >>> for h in db.sorted_by(high_grade_meters, reverse=True):
        ...     print(f"{h.hole_id}: {high_grade_meters(h)}m of high grade")
        """
        # Get all holes
        holes = [self[hole_id] for hole_id in self.list_holes()]

        # Define sort key function
        if key is None:
            # Sort by hole_id (default)
            sort_key = lambda h: h.hole_id
        elif isinstance(key, str):
            # Sort by collar column
            def sort_key(h):
                try:
                    return h.collar[key].iloc[0]
                except (KeyError, IndexError):
                    logger.warning(
                        f"Column '{key}' not found in collar for hole {h.hole_id}, using 0"
                    )
                    return 0

        elif callable(key):
            # Use custom function
            sort_key = key
        else:
            raise TypeError(f"key must be str, callable, or None, got {type(key)}")

        # Sort and yield
        try:
            sorted_holes = sorted(holes, key=sort_key, reverse=reverse)
            for hole in sorted_holes:
                yield hole
        except Exception as e:
            logger.error(f"Error sorting holes: {e}")
            raise

    def add_interval_table(
        self,
        name: str,
        df: Union[pd.DataFrame, str],
        column_mapping: Dict[str, str] = {},
    ):
        """Register a new interval table.

        Parameters
        ----------
        name : str
            Unique name for the table
        df : pd.DataFrame, str
            Interval data or path to file with required columns: HOLE_ID, FROM, TO
        column_mapping : dict, optional
            Mapping of CSV column names to required DrillholeDatabase columns.
            passes to pandas rename.
        """
        if isinstance(df, str):
            # Load from CSV file
            df = pd.read_csv(df)
        
        if type(df) is not pd.DataFrame:
            raise TypeError("df must be a pandas DataFrame, or a path to a CSV file")
        df = df.rename(columns=column_mapping)

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

    def add_point_table(
        self,
        name: str,
        df: Union[pd.DataFrame, str],
        column_mapping: Dict[str, str] = {},
    ):
        """Register a new point table.

        Parameters
        ----------
        name : str
            Unique name for the table
        df : pd.DataFrame, str
            Point data or path to file with required columns: HOLE_ID, DEPTH
        column_mapping : dict, optional
            Mapping of CSV column names to required DrillholeDatabase columns.
            passes to pandas rename.
        """
        if isinstance(df, str):
            # Load from CSV file
            df = pd.read_csv(df)
        if type(df) is not pd.DataFrame:
            raise TypeError("df must be a pandas DataFrame, or a path to a CSV file")
        df = df.rename(columns=column_mapping)
        
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
        merged_hole_ids = pd.merge(
            self.collar[[DhConfig.holeid]],
            self.survey[[DhConfig.holeid]].drop_duplicates(),
            on=DhConfig.holeid,
            how="inner",
        )
        return sorted(merged_hole_ids[DhConfig.holeid].tolist())

    def extent(self, sampling: float = 1.0, buffer: float = 0.0) -> BoundingBox:
        """Return spatial extent of all drillholes.
        Parameters
        ----------
        sampling : float, default 1.0
            Sampling interval in meters for calculating extent from traces.
            Higher values are faster but less accurate.
        buffer : float, default 0.0
            Buffer in meters to add to each side of the extent.
        Returns
        -------
        BoundingBox
            The spatial extent of all drillholes as a BoundingBox object.
        """
        all_traces = pd.concat(
            [h.trace(sampling).trace_points for h in self],
        )
        bb = (
            BoundingBox()
            .fit(all_traces[["x", "y", "z"]].values, local_coordinate=True)
            .with_buffer(buffer)
        )

        return bb

    def filter(
        self,
        holes: Optional[List[str]] = None,
        bbox: Optional[Tuple[float, float, float, float]] = None,
        depth_range: Optional[Tuple[float, float]] = None,
        expr: Optional[Union[str, Callable]] = None,
    ) -> "DrillholeDatabase":
        """Return a filtered DrillholeDatabase.

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

        Examples
        --------
        # Filter to keep only holes where all intervals in 'lithology' table have NaN for 'LITHO' column
        >>> nan_holes = db.collar.loc[
        ...     db.intervals['lithology']
        ...         .groupby(DhConfig.holeid)['LITHO']
        ...         .apply(lambda s: s.isna().all())
        ...         .pipe(lambda x: x[x].index)
        ... ].index.tolist()
        >>> db_nan = db.filter(holes=nan_holes)

        # Or using a callable:
        >>> def all_nan_litho(df):
        ...     return df.groupby(DhConfig.holeid)['LITHO'].apply(lambda s: s.isna().all())
        >>> nan_holes = all_nan_litho(db.intervals['lithology'])
        >>> db_nan = db.filter(holes=nan_holes[nan_holes].index.tolist())
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

        # Create new database instance with same db_config
        new_db = DrillholeDatabase(filtered_collar, filtered_survey, db_config=self.db_config)

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

            # add the table to the new db even if it is empty as we want to have the same tables
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

    def get_table(self, table_name: str, table_type: str = "point") -> pd.DataFrame:
        """Retrieve a table by name and type.

        Parameters
        ----------
        table_name : str
            Name of the interval or point table to retrieve
        table_type : str, default 'point'
            Type of table ('point' or 'interval')

        Returns
        -------
        pd.DataFrame
            The requested table DataFrame

        Raises
        ------
        ValueError
            If the specified table does not exist

        Notes
        -----
        If the table name does not exist in the specified type, the method
        will check the other type before raising an error.
        """
        tables = None
        if table_type == "point":
            tables = self.points
        elif table_type == "interval":
            tables = self.intervals

        if tables is None:
            if table_name in self.intervals:
                tables = self.intervals
            elif table_name in self.points:
                tables = self.points
        if tables is None:
            raise ValueError(f"table not found in {table_type} tables")

        if table_name not in tables:
            raise KeyError(f"Table '{table_name}' not found in {table_type} tables")

        table = tables[table_name]
        return table

    def validate_numerical_columns(
        self,
        table_name: str,
        columns: List[str],
        table_type: str = "point",
        allow_negative: bool = False,
    ) -> "DrillholeDatabase":
        """Validate and clean numerical columns in a table.

        This method:
        - Validates that specified columns are numerical
        - Replaces non-positive values (or negative values if allow_negative=False) with NaN
        - Ensures columns are converted to numerical type

        Parameters
        ----------
        table_name : str
            Name of the interval or point table to validate
        columns : list[str]
            List of column names to validate
        table_type : str, default 'point'
            Type of table ('point' or 'interval')
        allow_negative : bool, default False
            If False, replaces values <= 0 with NaN. If True, only replaces negative values with NaN.

        Returns
        -------
        DrillholeDatabase
            Self, to allow method chaining
        """
        # Determine which table dictionary to use
        table = self.get_table(table_name, table_type)  # Validate table exists

        # Process each column
        for col in columns:
            if col not in table.columns:
                logger.warning(f"Column '{col}' not found in table '{table_name}', skipping")
                continue

            # Convert to numeric, coercing errors to NaN
            table[col] = pd.to_numeric(table[col], errors="coerce")

            # Replace non-positive or negative values with NaN
            if not allow_negative:
                # Only replace negative values
                table.loc[table[col] <= 0, col] = np.nan

        return self

    def filter_by_nan_threshold(
        self, table_name: str, columns: List[str], threshold: float, table_type: str = "point"
    ) -> "DrillholeDatabase":
        """Filter rows based on the proportion of non-NaN values in specified columns.

        This method removes rows where the proportion of valid (non-NaN) values
        in the specified columns is below the threshold.

        Parameters
        ----------
        table_name : str
            Name of the interval or point table to filter
        columns : list[str]
            List of column names to check for NaN values
        threshold : float
            Minimum proportion of non-NaN values required (0.0 to 1.0).
            For example, 0.5 means at least 50% of the columns must have valid values.
        table_type : str, default 'point'
            Type of table ('point' or 'interval')

        Returns
        -------
        DrillholeDatabase
            New filtered database instance with rows removed based on threshold

        Examples
        --------
        >>> # Keep only rows where at least 80% of assay columns have valid values
        >>> db_filtered = db.filter_by_nan_threshold('assay', ['CU_PPM', 'AU_PPM', 'AG_PPM'], 0.8)

        >>> # Can be chained with other filters
        >>> db_filtered = db.filter(holes=['DH001', 'DH002']).filter_by_nan_threshold('assay', ['CU_PPM'], 0.5)
        """
        # Validate threshold
        if not 0.0 <= threshold <= 1.0:
            raise ValueError(f"threshold must be between 0.0 and 1.0, got {threshold}")

        table = self.get_table(table_name, table_type)  # Validate table exists

        # Check which columns exist
        existing_columns = [col for col in columns if col in table.columns]
        missing_columns = [col for col in columns if col not in table.columns]

        if missing_columns:
            logger.warning(f"Columns not found in table '{table_name}': {missing_columns}")

        if not existing_columns:
            raise ValueError(f"None of the specified columns found in table '{table_name}'")

        # Calculate proportion of non-NaN values for each row
        non_nan_count = table[existing_columns].notna().sum(axis=1)
        total_columns = len(existing_columns)
        non_nan_proportion = non_nan_count / total_columns

        # Create mask for rows that meet the threshold
        mask = non_nan_proportion >= threshold

        # Get the hole IDs that have data meeting the threshold
        filtered_table = table[mask].copy()

        # If the filtered table is empty, return an empty database
        if filtered_table.empty:
            # Create an empty database with the same structure
            empty_collar = self.collar.iloc[0:0].copy()
            empty_survey = self.survey.iloc[0:0].copy()
            new_db = DrillholeDatabase(empty_collar, empty_survey)
            return new_db

        # Get unique hole IDs from the filtered table
        hole_ids_to_keep = set(filtered_table[DhConfig.holeid].unique())

        # Use the existing filter method to filter by these holes
        new_db = self.filter(holes=list(hole_ids_to_keep))

        # Update the specific table in the new database
        if table_type == "point":
            new_db.points[table_name] = filtered_table
        else:
            new_db.intervals[table_name] = filtered_table

        return new_db

    def validate(self) -> bool:
        """Perform schema and consistency checks.

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
        properties: Optional[List[str]] = None,
    ):
        """Return a PyVista MultiBlock object containing all drillholes as tubes.

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
        """Desurvey interval data for all holes to get 3D coordinates.

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
                if DhConfig.debug:
                    raise e
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
        """Desurvey point data for all holes to get 3D coordinates.

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
            return pd.DataFrame(
                columns=[DhConfig.holeid, DhConfig.depth, "x", "y", "z", "DIP", "AZIMUTH"]
            )

        return pd.concat(desurveyed_points, ignore_index=True)

    def alpha_beta_to_orientation(self, table_name: str, fmt: str = "vector") -> pd.DataFrame:
        """Desurvey point table, and add strike and dip column using alpha and beta angles.

        Parameters
        ----------
        table_name : str
            Name of the point table to process
        fmt : str, default 'vector'
            Format of the output orientation. Options are:
            - 'vector': returns the components of the normal vector nx, ny, nz
            - 'strike_dip': returns strike and dip as columns 'STRIKE' and 'DIP'
            - 'dip_direction_dip': returns dip direction and dip as columns 'DIP_DIRECTION' and 'DIP'

        Returns
        -------
        pd.DataFrame
            Desurveyed point data with added orientation columns
        Raises
        ------
        KeyError
            If required columns are missing
        ValueError
            If fmt is not recognized
        """
        if table_name not in self.points:
            raise KeyError(f"Point table '{table_name}' not found")
        if DhConfig.alpha not in self.points[table_name].columns:
            raise KeyError(f"Column '{DhConfig.alpha}' not found in point table '{table_name}'")
        if DhConfig.beta not in self.points[table_name].columns:
            raise KeyError(f"Column '{DhConfig.beta}' not found in point table '{table_name}'")
        if fmt not in ["vector", "strike_dip", "dip_direction_dip"]:
            raise ValueError(
                f"fmt must be 'vector', 'strike_dip', or 'dip_direction_dip', got '{fmt}'"
            )
        if fmt == "vector":
            columns = ["nx", "ny", "nz"]
        elif fmt == "strike_dip":
            columns = ["STRIKE", "DIP"]
        else:  # fmt == 'dip_direction_dip'
            columns = ["DIP_DIRECTION", "DIP"]
        desurveyed_points = self.desurvey_points(table_name)
        desurveyed_points = desurveyed_points.copy()
        desurveyed_points[columns] = np.nan
        if desurveyed_points.empty:
            logger.warning(f"Point table '{table_name}' is empty after desurveying")
            return desurveyed_points

        desurveyed_points = alphaBeta2vector(desurveyed_points)
        if fmt == "vector":
            return desurveyed_points
        else:
            strike_dip = normal_vector_to_strike_and_dip(
                desurveyed_points[["nx", "ny", "nz"]].values
            )
            if fmt == "strike_dip":
                desurveyed_points[["STRIKE", "DIP"]] = strike_dip
                return desurveyed_points
            else:  # dip and dip_dir
                dip_direction = (strike_dip[:, 0] + 90) % 360
                desurveyed_points[["DIP_DIRECTION", "DIP"]] = np.column_stack(
                    (dip_direction, strike_dip[:, 1])
                )
                return desurveyed_points

    def resample_interval_to_depths(
        self, interval_table_name: str, new_interval: float
    ) -> pd.DataFrame:
        """
        Resample interval data to match a new set of depths.

        Parameters
        ----------
        interval_table_name : str
            Name of the interval table to resample
        new_depths : pd.Series
            Series of new depths to match

        Returns
        -------
        pd.DataFrame
            Resampled interval data
        """
        if interval_table_name not in self.intervals:
            raise KeyError(f"Interval table '{interval_table_name}' not found")
        cols = [
            c
            for c in self.intervals[interval_table_name].columns.tolist()
            if c != DhConfig.depth
            and c != DhConfig.sample_from
            and c != DhConfig.sample_to
            and c != DhConfig.holeid
        ]

        resampled_intervals = []

        # Process each hole
        for hole_id in self.list_holes():
            # tr/y:
            drillhole = self[hole_id]
            hole_intervals = drillhole.resample(
                interval_table_name, cols=cols, new_interval=new_interval
            )
            if not hole_intervals.empty:
                resampled_intervals.append(hole_intervals)
            # except Exception as e:
            #     logger.warning(f"Failed to resample intervals for hole {hole_id}: {e}")
            #     continue

        if not resampled_intervals:
            # Return empty DataFrame with expected structure
            return pd.DataFrame(
                columns=[
                    DhConfig.holeid,
                    DhConfig.sample_from,
                    DhConfig.sample_to,
                    DhConfig.depth_mid,
                ]
            )

        return pd.concat(resampled_intervals, ignore_index=True)
