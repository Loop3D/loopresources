"""
DrillHoleDatabase - A clean implementation based on AGENTS.md specifications.

This module provides a modern, pandas-native interface for drillhole data management
with filtering, validation, and export capabilities.
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Tuple, Union, Callable
import logging

from .dhconfig import DhConfig

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

        # Filter collar and survey for this hole
        collar_mask = self.database.collar[DhConfig.holeid] == hole_id
        survey_mask = self.database.survey[DhConfig.holeid] == hole_id

        self.collar = self.database.collar[collar_mask].copy()
        self.survey = self.database.survey[survey_mask].copy()

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
            table = self.database.intervals[propertyname]
            mask = table[DhConfig.holeid] == self.hole_id
            return table[mask].copy()

        # Check points
        if propertyname in self.database.points:
            table = self.database.points[propertyname]
            mask = table[DhConfig.holeid] == self.hole_id
            return table[mask].copy()

        raise KeyError(f"Table '{propertyname}' not found in intervals or points")

    def interval_tables(self) -> Dict[str, pd.DataFrame]:
        """Return all interval tables for this hole."""
        result = {}
        for name, table in self.database.intervals.items():
            mask = table[DhConfig.holeid] == self.hole_id
            filtered = table[mask].copy()
            if not filtered.empty:
                result[name] = filtered
        return result

    def point_tables(self) -> Dict[str, pd.DataFrame]:
        """Return all point tables for this hole."""
        result = {}
        for name, table in self.database.points.items():
            mask = table[DhConfig.holeid] == self.hole_id
            filtered = table[mask].copy()
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

    def vtk(self, newinterval: Union[float, np.ndarray] = 1.0, radius: float = 0.1):
        """
        Return a PyVista tube object representing the drillhole trace.

        Parameters
        ----------
        newinterval : float or array-like, default 1.0
            Step size for interpolation along hole depth, or specific depths to sample
        radius : float, default 0.1
            Radius of the tube representation

        Returns
        -------
        pyvista.PolyData
            PyVista tube object of the drillhole trace
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


class DrillholeDatabase:
    """
    Main container for all drillhole data.

    Stores global data as pandas DataFrames and dictionaries following
    the specification in AGENTS.md.
    """

    def __init__(self, collar: pd.DataFrame, survey: pd.DataFrame):
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
        """
        self.collar = collar.copy()
        self.survey = survey.copy()
        self.intervals: Dict[str, pd.DataFrame] = {}
        self.points: Dict[str, pd.DataFrame] = {}

        # Validate input data
        self._validate_collar()
        self._validate_survey()

        # Convert angles if needed
        self._normalize_angles()

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

    def vtk(self, newinterval: Union[float, np.ndarray] = 1.0, radius: float = 0.1):
        """
        Return a PyVista MultiBlock object containing all drillholes as tubes.

        Parameters
        ----------
        newinterval : float or array-like, default 1.0
            Step size for interpolation along hole depth, or specific depths to sample
        radius : float, default 0.1
            Radius of the tube representation for each drillhole

        Returns
        -------
        pyvista.MultiBlock
            PyVista MultiBlock object containing all drillhole tubes
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
                tube = drillhole.vtk(newinterval=newinterval, radius=radius)
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
