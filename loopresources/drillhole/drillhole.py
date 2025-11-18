"""DrillHole - A clean implementation based on AGENTS.md specifications.

This module provides a modern, pandas-native interface for drillhole data management
with filtering, validation, and export capabilities.
"""

import pandas as pd
import numpy as np
from numpy.typing import ArrayLike
from scipy.interpolate import interp1d
from typing import Dict, List, Optional, Union
import logging

from loopresources.drillhole.math import slerp, trendandplunge2vector, vector2trendandplunge

from .dhconfig import DhConfig
from .desurvey import desurvey

from typing import TYPE_CHECKING, Callable

if TYPE_CHECKING:
    from .drillholedatabase import DrillholeDatabase  # Only imported for type checking

logger = logging.getLogger(__name__)


class DrillHoleTrace:
    """Container providing interpolated trace access for a drillhole."""

    def __init__(self, drillhole: "DrillHole", *, interval: float = 1.0):
        """Create a DrillHoleTrace for a DrillHole using a specified sampling interval."""
        trace_points = desurvey(drillhole.collar, drillhole.survey, interval)
        self.trace_points = trace_points
        self.x_interpolator = interp1d(
            trace_points[DhConfig.depth], trace_points["x"], fill_value="extrapolate"
        )
        self.y_interpolator = interp1d(
            trace_points[DhConfig.depth], trace_points["y"], fill_value="extrapolate"
        )
        self.z_interpolator = interp1d(
            trace_points[DhConfig.depth], trace_points["z"], fill_value="extrapolate"
        )
        unit_vectors = trendandplunge2vector(
            trace_points[DhConfig.azimuth], trace_points[DhConfig.dip]
        )

        def orientation_interpolator(depth):
            
            new_vectors = slerp(unit_vectors, trace_points[DhConfig.depth].values, depth)
            new_azimuth, new_dip = vector2trendandplunge(new_vectors)
            return new_azimuth, new_dip

        self.orientation_interpolator = orientation_interpolator

    def __call__(self, newinterval: Optional[Union[np.ndarray, float]] = 1.0):
        """Return resampled trace as a DataFrame for given interval or depths."""
        if not hasattr(newinterval, "__len__"):  # is it an array?
            newdepth = np.arange(
                0,
                self.trace_points[DhConfig.depth].max(),
                newinterval,
            )
        else:  # if its an array just use the array values
            newdepth = newinterval
        # avoid duplicate call
        azi, dip = self.orientation_interpolator(newdepth)
        return pd.DataFrame(
            {
                DhConfig.depth: newdepth,
                "x": self.x_interpolator(newdepth),
                "y": self.y_interpolator(newdepth),
                "z": self.z_interpolator(newdepth),
                "dip": dip,
                "azimuth": azi,
            }
        )

    def depth_at(self, x: float, y: float, z: float) -> float:
        """Return depth along hole closest to a given XYZ point.

        Parameters
        ----------
        x, y, z : float
            Coordinates of the point

        Returns
        -------
        float
            Depth along hole closest to the point
        """
        distances = np.sqrt(
            (self.trace_points["x"] - x) ** 2
            + (self.trace_points["y"] - y) ** 2
            + (self.trace_points["z"] - z) ** 2
        )
        closest_idx = distances.idxmin()
        return self.trace_points.loc[closest_idx, DhConfig.depth]

    def find_implicit_function_intersection(
        self, function: Callable[[ArrayLike], ArrayLike]
    ) -> pd.DataFrame:
        """Find intersection of drillhole trace with an implicit function.

        The provided function may be vectorised (accepting an Nx3 array and returning N values)
        or accept separate x,y,z arrays. Returns DataFrame with columns: depth, x, y, z.
        """
        pts = self.trace_points
        coords = np.vstack([pts["x"].values, pts["y"].values, pts["z"].values]).T

        # Call the function, trying vectorised signature first, then per-coordinate
        try:
            values = function(coords)
        except Exception:
            try:
                values = function(pts["x"].values, pts["y"].values, pts["z"].values)
            except Exception as e:
                raise RuntimeError(f"Implicit function call failed: {e}")

        values = np.asarray(values).ravel()
        if values.size != len(pts):
            raise ValueError("Implicit function must return one value per trace point")

        depths = pts[DhConfig.depth].values

        intersections = []

        # Handle exact zeros first
        zero_idxs = np.where(np.isclose(values, 0.0))[0]
        for idx in zero_idxs:
            d = float(depths[idx])
            intersections.append(
                {
                    DhConfig.depth: d,
                    "x": float(self.x_interpolator(d)),
                    "y": float(self.y_interpolator(d)),
                    "z": float(self.z_interpolator(d)),
                }
            )

        # Find sign changes (ignore intervals involving NaN)
        s = np.sign(values)
        s[np.isnan(values)] = 0
        sign_change_idxs = np.where(s[:-1] * s[1:] < 0)[0]

        for idx in sign_change_idxs:
            v1 = float(values[idx])
            v2 = float(values[idx + 1])
            d1 = float(depths[idx])
            d2 = float(depths[idx + 1])

            if np.isclose(v2 - v1, 0.0):
                # Degenerate interval, skip
                continue

            # Linear interpolation for depth at root
            depth_intersect = d1 + (0.0 - v1) * (d2 - d1) / (v2 - v1)

            intersections.append(
                {
                    DhConfig.depth: float(depth_intersect),
                    "x": float(self.x_interpolator(depth_intersect)),
                    "y": float(self.y_interpolator(depth_intersect)),
                    "z": float(self.z_interpolator(depth_intersect)),
                }
            )

        if not intersections:
            # Return empty DataFrame with expected columns
            return pd.DataFrame(columns=[DhConfig.depth, "x", "y", "z"])

        df = pd.DataFrame(intersections)
        # Remove potential duplicate depths and sort
        df = (
            df.drop_duplicates(subset=[DhConfig.depth])
            .sort_values(by=DhConfig.depth)
            .reset_index(drop=True)
        )
        return df


class DrillHole:
    """A view of the DrillholeDatabase for a single HOLE_ID.

    Provides per-hole access, sampling, and visualization.
    """

    def __init__(self, database: "DrillholeDatabase", hole_id: str):
        """Initialize DrillHole view.

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

    def __repr__(self) -> str:
        """Return a concise representation of the DrillHole."""
        total_depth = self.collar[DhConfig.total_depth].values[0]
        return f"DrillHole(hole_id='{self.hole_id}', depth={total_depth:.2f}m)"

    def __str__(self) -> str:
        """Return a detailed string representation of the DrillHole."""
        # Get basic hole information
        total_depth = self.collar[DhConfig.total_depth].values[0]
        collar_x = self.collar[DhConfig.x].values[0]
        collar_y = self.collar[DhConfig.y].values[0]
        collar_z = self.collar[DhConfig.z].values[0]

        # Calculate average azimuth and dip from survey data
        avg_azimuth = self.survey[DhConfig.azimuth].mean()
        avg_dip = self.survey[DhConfig.dip].mean()

        # Convert to degrees if values are in radians (small values suggest radians)
        if abs(avg_azimuth) < 2 * np.pi and abs(avg_dip) < np.pi:
            # Likely in radians, convert to degrees
            avg_azimuth_deg = np.rad2deg(avg_azimuth)
            avg_dip_deg = np.rad2deg(avg_dip)
        else:
            avg_azimuth_deg = avg_azimuth
            avg_dip_deg = avg_dip

        # Get attached tables
        interval_tables = list(self.interval_tables().keys())
        point_tables = list(self.point_tables().keys())

        # Build the string representation
        lines = [
            f"DrillHole: {self.hole_id}",
            f"{'=' * (11 + len(self.hole_id))}",
            f"Location: X={collar_x:.2f}, Y={collar_y:.2f}, Z={collar_z:.2f}",
            f"Total Depth: {total_depth:.2f}m",
            f"Average Azimuth: {avg_azimuth_deg:.2f}°",
            f"Average Dip: {avg_dip_deg:.2f}°",
        ]

        # Add interval tables information
        if interval_tables:
            lines.append(f"\nInterval Tables ({len(interval_tables)}):")
            for table_name in interval_tables:
                table = self[table_name]
                num_intervals = len(table)
                # Get non-standard columns (exclude HOLEID, SAMPFROM, SAMPTO, DEPTH)
                data_cols = [
                    col
                    for col in table.columns
                    if col
                    not in [
                        DhConfig.holeid,
                        DhConfig.sample_from,
                        DhConfig.sample_to,
                        DhConfig.depth,
                    ]
                ]

                lines.append(f"  - {table_name}: {num_intervals} intervals")

                # Add statistics for numerical columns
                for col in data_cols:
                    if pd.api.types.is_numeric_dtype(table[col]):
                        non_null = table[col].notna().sum()
                        if non_null > 0:
                            mean_val = table[col].mean()
                            min_val = table[col].min()
                            max_val = table[col].max()
                            lines.append(
                                f"    • {col}: mean={mean_val:.2f}, min={min_val:.2f}, max={max_val:.2f} (n={non_null})"
                            )
                        else:
                            lines.append(f"    • {col}: all null")
                    else:
                        # For categorical data, show unique values
                        unique_vals = table[col].nunique()
                        non_null = table[col].notna().sum()
                        lines.append(f"    • {col}: {unique_vals} unique values (n={non_null})")
        else:
            lines.append("\nInterval Tables: None")

        # Add point tables information
        if point_tables:
            lines.append(f"\nPoint Tables ({len(point_tables)}):")
            for table_name in point_tables:
                table = self[table_name]
                num_points = len(table)
                # Get non-standard columns
                data_cols = [
                    col for col in table.columns if col not in [DhConfig.holeid, DhConfig.depth]
                ]

                lines.append(f"  - {table_name}: {num_points} points")

                # Add statistics for numerical columns
                for col in data_cols:
                    if pd.api.types.is_numeric_dtype(table[col]):
                        non_null = table[col].notna().sum()
                        if non_null > 0:
                            mean_val = table[col].mean()
                            min_val = table[col].min()
                            max_val = table[col].max()
                            lines.append(
                                f"    • {col}: mean={mean_val:.2f}, min={min_val:.2f}, max={max_val:.2f} (n={non_null})"
                            )
                        else:
                            lines.append(f"    • {col}: all null")
                    else:
                        unique_vals = table[col].nunique()
                        non_null = table[col].notna().sum()
                        lines.append(f"    • {col}: {unique_vals} unique values (n={non_null})")
        else:
            lines.append("\nPoint Tables: None")

        return "\n".join(lines)

    def __getitem__(self, propertyname: str) -> pd.DataFrame:
        """Return a single interval or point table for this hole.

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

    def trace(self, step: float = 1.0) -> DrillHoleTrace:
        """Return the interpolated XYZ trace of the hole.

        Parameters
        ----------
        step : float, default 1.0
            Step size for interpolation along hole depth

        Returns
        -------
        DrillHoleTrace
            Interpolated trace of the drill hole
        """
        return DrillHoleTrace(self, interval=step)

    def find_implicit_function_intersection(
        self, function: Callable[[ArrayLike], ArrayLike], step: float = 1.0
    ) -> pd.DataFrame:
        """Find intersection of drillhole trace with an implicit function.

        The provided function may be vectorised (accepting an Nx3 array and returning N values)
        or accept separate x,y,z arrays. Returns DataFrame with columns: depth, x, y, z.

        Parameters
        ----------
        function : Callable[[ArrayLike], ArrayLike]
            Implicit function defining the surface to intersect with
        step : float, default 1.0
            Step size for interpolation along hole depth

        Returns
        -------
        pd.DataFrame
            DataFrame of intersection points with columns: depth, x, y, z
        """
        trace = self.trace(step)
        df = trace.find_implicit_function_intersection(function)
        df[DhConfig.holeid] = self.hole_id
        return df

    def depth_at(self, x: float, y: float, z: float) -> float:
        """Return depth along hole closest to a given XYZ point.

        Parameters
        ----------
        x, y, z : float
            Coordinates of the point

        Returns
        -------
        float
            Depth along hole closest to the point
        """
        return self.trace().depth_at(x, y, z)

    def vtk(
        self,
        newinterval: Union[float, np.ndarray] = 1.0,
        radius: float = 0.1,
        properties: Optional[List[str]] = None,
    ):
        """Return a PyVista tube object representing the drillhole trace.

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

        trace = self.trace(newinterval).trace_points

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

                    # If the property table is empty for this hole, create a dummy interval with NaN values
                    if prop_table.empty:
                        # Check if the table exists in the database at all
                        if prop_name in self.database.intervals:
                            # Get column names from the global table to maintain consistency
                            global_table = self.database.intervals[prop_name]
                            cols_to_resample = [
                                col
                                for col in global_table.columns
                                if col
                                not in [
                                    DhConfig.holeid,
                                    DhConfig.sample_from,
                                    DhConfig.sample_to,
                                    DhConfig.depth,
                                ]
                            ]

                            if cols_to_resample:
                                # Get the hole's total depth from collar
                                total_depth = self.collar[DhConfig.total_depth].values[0]

                                # Create a dummy interval spanning the entire hole with NaN values
                                prop_table = pd.DataFrame(
                                    {
                                        DhConfig.holeid: [self.hole_id],
                                        DhConfig.sample_from: [0.0],
                                        DhConfig.sample_to: [total_depth],
                                        **{col: [np.nan] * 1 for col in cols_to_resample},
                                    }
                                )

                                logger.debug(
                                    f"Property table '{prop_name}' is empty for hole '{self.hole_id}', "
                                    f"using NaN values for entire hole depth (0-{total_depth}m)."
                                )
                            else:
                                logger.warning(
                                    f"No data columns found in property table '{prop_name}', skipping"
                                )
                                continue
                        else:
                            logger.warning(
                                f"Property table '{prop_name}' not found in database. "
                                f"Available tables: {list(self.database.intervals.keys())}"
                            )
                            continue

                    # Get all columns except the standard ones
                    cols_to_resample = [
                        col
                        for col in prop_table.columns
                        if col
                        not in [
                            DhConfig.holeid,
                            DhConfig.sample_from,
                            DhConfig.sample_to,
                            DhConfig.depth,
                        ]
                    ]

                    if not cols_to_resample:
                        logger.warning(
                            f"No data columns found in property table '{prop_name}', skipping"
                        )
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
                            if col in polydata.cell_data:
                                logger.warning(
                                    f"Overwriting existing cell data for property '{col}'"
                                )
                            polydata.cell_data[col] = cell_values

                except KeyError as e:
                    logger.warning(
                        f"Property table '{prop_name}' not found for hole '{self.hole_id}'. "
                        f"Available tables: {list(self.database.intervals.keys())}. Error: {e}"
                    )
                except Exception as e:
                    logger.warning(f"Failed to add property '{prop_name}': {e}")

        # Return as tube
        return polydata.tube(radius=radius)

    def desurvey_intervals(self, interval_table_name: str) -> pd.DataFrame:
        """Desurvey interval data to get 3D coordinates for FROM and TO depths.

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
        mid_depths = (from_depths + to_depths) / 2
        # Desurvey at all depths
        trace = self.trace()
        desurveyed_points_to = trace(to_depths)
        desurveyed_points_from = trace(from_depths)
        desurveyed_points_mid = trace(mid_depths)

        # Create result dataframe with original data
        result = intervals.copy()

        # Add FROM coordinates
        result["x_from"] = desurveyed_points_from["x"].values
        result["y_from"] = desurveyed_points_from["y"].values
        result["z_from"] = desurveyed_points_from["z"].values

        # Add TO coordinates
        result["x_to"] = desurveyed_points_to["x"].values
        result["y_to"] = desurveyed_points_to["y"].values
        result["z_to"] = desurveyed_points_to["z"].values

        # Add midpoint coordinates
        mid_depths = (from_depths + to_depths) / 2
        result["x_mid"] = desurveyed_points_mid["x"].values
        result["y_mid"] = desurveyed_points_mid["y"].values
        result["z_mid"] = desurveyed_points_mid["z"].values
        result["depth_mid"] = mid_depths

        return result

    def desurvey_points(self, point_table_name: str) -> pd.DataFrame:
        """Desurvey point data to get 3D coordinates.

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
        trace = self.trace()
        desurveyed_points = trace(depths)

        # Create result dataframe with original data
        result = points.copy()

        # Add coordinates
        result["x"] = desurveyed_points["x"].values
        result["y"] = desurveyed_points["y"].values
        result["z"] = desurveyed_points["z"].values
        result["DIP"] = np.rad2deg(desurveyed_points["dip"].values)
        result["AZIMUTH"] = np.rad2deg(desurveyed_points["azimuth"].values)
        return result

    def resample(
        self, interval_table_name: str, cols: List[str], new_interval: float = 1.0
    ) -> pd.DataFrame:
        """Resample interval data onto a new regular interval.

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
