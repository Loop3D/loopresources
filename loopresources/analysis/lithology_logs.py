"""LithologyLogs - Preprocessing tools for lithological drillhole data.

This module provides tools to extract contacts, apply smoothing filters,
and identify lithological pairs from drillhole interval data.
"""

import pandas as pd
from typing import List, Optional
from scipy.ndimage import uniform_filter1d
import logging

from ..drillhole.dhconfig import DhConfig

logger = logging.getLogger(__name__)


class LithologyLogs:
    """Preprocessing tools for lithological drillhole logs.

    This class provides methods to extract contacts between lithologies,
    apply smoothing filters, and identify lithological pairs. Results
    can be stored as new tables in the drillhole database.

    Parameters
    ----------
    database : DrillholeDatabase
        The drillhole database containing the data
    interval_table_name : str
        Name of the interval table containing lithology data
    lithology_column : str, default 'LITHO'
        Name of the column containing lithology labels
    """

    def __init__(self, database, interval_table_name: str, lithology_column: str = "LITHO"):
        """Initialize LithologyLogs with a drillhole database.

        Parameters
        ----------
        database : DrillholeDatabase
            The drillhole database
        interval_table_name : str
            Name of the interval table containing lithology data
        lithology_column : str, default 'LITHO'
            Name of the column containing lithology labels
        """
        self.database = database
        self.interval_table_name = interval_table_name
        self.lithology_column = lithology_column

        # Validate that the table exists
        if interval_table_name not in database.intervals:
            raise ValueError(f"Interval table '{interval_table_name}' not found in database")

        # Validate that the lithology column exists
        table = database.intervals[interval_table_name]
        if lithology_column not in table.columns:
            raise ValueError(
                f"Column '{lithology_column}' not found in table '{interval_table_name}'"
            )

    def extract_contacts(self, store_as: Optional[str] = None) -> pd.DataFrame:
        """Extract all contacts between different lithologies.

        A contact is defined as the boundary between two different lithology intervals
        within a single drillhole.

        Parameters
        ----------
        store_as : str, optional
            If provided, store the result as a point table with this name

        Returns
        -------
        pd.DataFrame
            DataFrame with columns: HOLEID, DEPTH, LITHO_ABOVE, LITHO_BELOW
            where DEPTH is the contact depth and LITHO_ABOVE/LITHO_BELOW are
            the lithologies on either side
        """
        contacts = []
        table = self.database.intervals[self.interval_table_name]

        # Process each hole separately
        for hole_id in table[DhConfig.holeid].unique():
            hole_data = table[table[DhConfig.holeid] == hole_id].copy()

            # Sort by depth
            hole_data = hole_data.sort_values(DhConfig.sample_from)

            # Find contacts between adjacent intervals
            for i in range(len(hole_data) - 1):
                current = hole_data.iloc[i]
                next_interval = hole_data.iloc[i + 1]

                # Check if lithologies are different and intervals are adjacent
                if current[self.lithology_column] != next_interval[self.lithology_column]:
                    # Contact at the boundary
                    contact_depth = current[DhConfig.sample_to]

                    contacts.append(
                        {
                            DhConfig.holeid: hole_id,
                            DhConfig.depth: contact_depth,
                            "LITHO_ABOVE": current[self.lithology_column],
                            "LITHO_BELOW": next_interval[self.lithology_column],
                        }
                    )

        result = pd.DataFrame(contacts)

        # Store if requested
        if store_as is not None and not result.empty:
            self.database.add_point_table(store_as, result)
            logger.info(f"Stored {len(result)} contacts as point table '{store_as}'")

        return result

    def extract_basal_contacts(
        self, lithology_order: List[str], store_as: Optional[str] = None
    ) -> pd.DataFrame:
        """Extract basal contacts for a specified lithological order.

        A basal contact is the bottom boundary of a lithology unit. This method
        extracts contacts where the lithology sequence matches the specified order.

        Parameters
        ----------
        lithology_order : list of str
            Ordered list of lithology names from top to bottom
        store_as : str, optional
            If provided, store the result as a point table with this name

        Returns
        -------
        pd.DataFrame
            DataFrame with columns: HOLEID, DEPTH, LITHO
            where DEPTH is the basal contact depth for each LITHO
        """
        basal_contacts = []
        table = self.database.intervals[self.interval_table_name]

        # Create a mapping of lithology to its order index
        litho_order_map = {litho: i for i, litho in enumerate(lithology_order)}

        # Process each hole separately
        for hole_id in table[DhConfig.holeid].unique():
            hole_data = table[table[DhConfig.holeid] == hole_id].copy()

            # Sort by depth
            hole_data = hole_data.sort_values(DhConfig.sample_from)

            # Find basal contacts that match the specified order
            for i in range(len(hole_data) - 1):
                current = hole_data.iloc[i]
                next_interval = hole_data.iloc[i + 1]

                current_litho = current[self.lithology_column]
                next_litho = next_interval[self.lithology_column]

                # Check if both lithologies are in the order
                if current_litho in litho_order_map and next_litho in litho_order_map:
                    # Check if the sequence follows the order
                    if litho_order_map[current_litho] < litho_order_map[next_litho]:
                        # Basal contact at the bottom of current lithology
                        basal_contacts.append(
                            {
                                DhConfig.holeid: hole_id,
                                DhConfig.depth: current[DhConfig.sample_to],
                                "LITHO": current_litho,
                            }
                        )

            # Add the basal contact for the last interval if it's in the order
            if len(hole_data) > 0:
                last = hole_data.iloc[-1]
                if last[self.lithology_column] in litho_order_map:
                    basal_contacts.append(
                        {
                            DhConfig.holeid: hole_id,
                            DhConfig.depth: last[DhConfig.sample_to],
                            "LITHO": last[self.lithology_column],
                        }
                    )

        result = pd.DataFrame(basal_contacts)

        # Store if requested
        if store_as is not None and not result.empty:
            self.database.add_point_table(store_as, result)
            logger.info(f"Stored {len(result)} basal contacts as point table '{store_as}'")

        return result

    def apply_smoothing_filter(
        self, window_size: int = 3, store_as: Optional[str] = None
    ) -> pd.DataFrame:
        """Apply a moving average smoothing filter to lithology intervals.

        This method smooths the lithology log by applying a moving average to
        the midpoint depths of intervals. Intervals shorter than a threshold
        may be merged with adjacent intervals based on the smoothed depths.

        Parameters
        ----------
        window_size : int, default 3
            Size of the smoothing window (number of intervals)
        store_as : str, optional
            If provided, store the result as an interval table with this name

        Returns
        -------
        pd.DataFrame
            DataFrame with smoothed lithology intervals
        """
        smoothed_data = []
        table = self.database.intervals[self.interval_table_name]

        # Process each hole separately
        for hole_id in table[DhConfig.holeid].unique():
            hole_data = table[table[DhConfig.holeid] == hole_id].copy()

            # Sort by depth
            hole_data = hole_data.sort_values(DhConfig.sample_from).reset_index(drop=True)

            if len(hole_data) < window_size:
                # If not enough data, return original
                smoothed_data.append(hole_data)
                continue

            # Calculate midpoint depths
            midpoints = (hole_data[DhConfig.sample_from] + hole_data[DhConfig.sample_to]) / 2.0

            # Apply uniform filter to midpoints
            smoothed_midpoints = uniform_filter1d(
                midpoints.values, size=window_size, mode="nearest"
            )

            # Calculate smoothed interval thicknesses
            thicknesses = hole_data[DhConfig.sample_to] - hole_data[DhConfig.sample_from]
            smoothed_thicknesses = uniform_filter1d(
                thicknesses.values, size=window_size, mode="nearest"
            )

            # Reconstruct intervals from smoothed midpoints and thicknesses
            smoothed_from = smoothed_midpoints - smoothed_thicknesses / 2.0
            smoothed_to = smoothed_midpoints + smoothed_thicknesses / 2.0

            # Create smoothed intervals
            smoothed_hole = hole_data.copy()
            smoothed_hole[DhConfig.sample_from] = smoothed_from
            smoothed_hole[DhConfig.sample_to] = smoothed_to

            smoothed_data.append(smoothed_hole)

        result = pd.concat(smoothed_data, ignore_index=True) if smoothed_data else pd.DataFrame()

        # Store if requested
        if store_as is not None and not result.empty:
            self.database.add_interval_table(store_as, result)
            logger.info(f"Stored smoothed intervals as '{store_as}'")

        return result

    def identify_lithological_pairs(self, store_as: Optional[str] = None) -> pd.DataFrame:
        """Identify all unique pairs of adjacent lithologies.

        This method finds all pairs of lithologies that appear adjacent to each
        other in the drillhole logs and counts their occurrences.

        Parameters
        ----------
        store_as : str, optional
            If provided, store the result as a point table with this name
            (note: this creates a contact table with pair information)

        Returns
        -------
        pd.DataFrame
            DataFrame with columns: LITHO_ABOVE, LITHO_BELOW, COUNT, HOLES
            where COUNT is the number of occurrences and HOLES is a list of
            hole IDs where this pair occurs
        """
        pairs = {}
        table = self.database.intervals[self.interval_table_name]

        # Process each hole separately
        for hole_id in table[DhConfig.holeid].unique():
            hole_data = table[table[DhConfig.holeid] == hole_id].copy()

            # Sort by depth
            hole_data = hole_data.sort_values(DhConfig.sample_from)

            # Find pairs between adjacent intervals
            for i in range(len(hole_data) - 1):
                current = hole_data.iloc[i]
                next_interval = hole_data.iloc[i + 1]

                litho_above = current[self.lithology_column]
                litho_below = next_interval[self.lithology_column]

                # Create a canonical pair key (sorted to avoid duplicates)
                pair_key = (litho_above, litho_below)

                if pair_key not in pairs:
                    pairs[pair_key] = {"count": 0, "holes": set()}

                pairs[pair_key]["count"] += 1
                pairs[pair_key]["holes"].add(hole_id)

        # Convert to DataFrame
        result_data = []
        for (litho_above, litho_below), data in pairs.items():
            result_data.append(
                {
                    "LITHO_ABOVE": litho_above,
                    "LITHO_BELOW": litho_below,
                    "COUNT": data["count"],
                    "HOLES": ",".join(sorted(data["holes"])),
                }
            )

        result = pd.DataFrame(result_data)

        # Sort by count descending
        if not result.empty:
            result = result.sort_values("COUNT", ascending=False).reset_index(drop=True)

        # Note: Pairs summary is not stored in the database as it's aggregate data
        # But we can store individual contact pairs if requested
        if store_as is not None and not result.empty:
            # Create a contacts table with pair information
            contacts = self.extract_contacts(store_as=None)
            if not contacts.empty:
                self.database.add_point_table(store_as, contacts)
                logger.info(f"Stored lithological contacts as point table '{store_as}'")

        return result

    def calculate_contact_orientations(
        self, radius: Optional[float] = None, min_neighbors: int = 3, store_as: Optional[str] = None
    ) -> pd.DataFrame:
        """Calculate the orientation of lithological contacts using nearest neighbors.

        This method:
        1. Extracts contacts and desurveys them to get 3D coordinates
        2. Uses a ball tree algorithm to find nearest neighbor contacts
        3. Fits a plane to the nearest neighbors to determine orientation
        4. Returns the normal vector of the fitted plane

        Parameters
        ----------
        radius : float, optional
            Search radius for nearest neighbors in 3D space.
            If None, uses the average spacing between drillhole collars.
        min_neighbors : int, default 3
            Minimum number of neighbors required to fit a plane.
            Must be at least 3.
        store_as : str, optional
            If provided, store the result as a point table with this name

        Returns
        -------
        pd.DataFrame
            DataFrame with columns: HOLEID, DEPTH, LITHO_ABOVE, LITHO_BELOW,
            x, y, z (contact location), nx, ny, nz (normal vector components),
            dip, azimuth (orientation in geological convention),
            n_neighbors (number of neighbors used)

        Notes
        -----
        The normal vector points in the direction perpendicular to the contact surface.
        Dip is measured from horizontal (0-90 degrees).
        Azimuth is the strike direction (0-360 degrees, North = 0).
        """
        if min_neighbors < 3:
            raise ValueError("min_neighbors must be at least 3 to fit a plane")

        # Extract contacts
        contacts = self.extract_contacts(store_as=None)

        if contacts.empty:
            logger.warning("No contacts found to calculate orientations")
            return pd.DataFrame()

        # Store contacts as a temporary point table for desurveying
        temp_table_name = "_temp_contacts_for_orientation"
        self.database.add_point_table(temp_table_name, contacts)

        try:
            # Desurvey contacts to get 3D coordinates
            desurveyed_contacts = self.database.desurvey_points(temp_table_name)

            if desurveyed_contacts.empty:
                logger.warning("No contacts could be desurveyed")
                return pd.DataFrame()

            # Calculate default radius if not provided
            if radius is None:
                # Calculate average spacing between drillhole collars
                collar_coords = self.database.collar[[DhConfig.x, DhConfig.y]].values
                if len(collar_coords) > 1:
                    from sklearn.neighbors import NearestNeighbors

                    nbrs = NearestNeighbors(n_neighbors=min(2, len(collar_coords)))
                    nbrs.fit(collar_coords)
                    distances, _ = nbrs.kneighbors(collar_coords)
                    # Use average of nearest neighbor distances, multiplied by factor for larger search
                    radius = float(distances[:, -1].mean() * 2.0)
                    logger.info(f"Using calculated radius: {radius:.2f}")
                else:
                    # Single hole, use a default
                    radius = 100.0
                    logger.info(f"Single hole detected, using default radius: {radius}")

            # Extract 3D coordinates
            coords = desurveyed_contacts[["x", "y", "z"]].values

            # Build ball tree for nearest neighbor search
            from sklearn.neighbors import BallTree

            tree = BallTree(coords, leaf_size=40)

            # Find neighbors within radius for each contact
            indices = tree.query_radius(coords, r=radius)

            # Calculate orientations
            import numpy as np

            orientations = []

            for i, neighbor_indices in enumerate(indices):
                # Need at least min_neighbors points (including self)
                if len(neighbor_indices) < min_neighbors:
                    continue

                # Get neighbor coordinates
                neighbor_coords = coords[neighbor_indices]

                # Fit plane using PCA
                # Center the points
                centroid = neighbor_coords.mean(axis=0)
                centered = neighbor_coords - centroid

                # Compute covariance matrix
                cov = np.cov(centered.T)

                # Eigenvalue decomposition
                eigenvalues, eigenvectors = np.linalg.eigh(cov)

                # Normal vector is the eigenvector with smallest eigenvalue
                normal = eigenvectors[:, 0]

                # Ensure consistent orientation (normal points upward)
                if normal[2] < 0:
                    normal = -normal

                # Normalize
                normal = normal / np.linalg.norm(normal)

                # Calculate dip and azimuth from normal vector
                # Dip: angle from horizontal
                dip = np.degrees(np.arcsin(abs(normal[2])))

                # Azimuth: strike direction (perpendicular to dip direction)
                # Calculate dip direction first
                dip_azimuth = np.degrees(np.arctan2(normal[0], normal[1]))
                if dip_azimuth < 0:
                    dip_azimuth += 360

                # Strike is perpendicular to dip direction
                azimuth = (dip_azimuth + 90) % 360

                # Store result
                orientations.append(
                    {
                        DhConfig.holeid: desurveyed_contacts.iloc[i][DhConfig.holeid],
                        DhConfig.depth: desurveyed_contacts.iloc[i][DhConfig.depth],
                        "LITHO_ABOVE": desurveyed_contacts.iloc[i]["LITHO_ABOVE"],
                        "LITHO_BELOW": desurveyed_contacts.iloc[i]["LITHO_BELOW"],
                        "x": coords[i, 0],
                        "y": coords[i, 1],
                        "z": coords[i, 2],
                        "nx": normal[0],
                        "ny": normal[1],
                        "nz": normal[2],
                        "dip": dip,
                        "azimuth": azimuth,
                        "n_neighbors": len(neighbor_indices),
                    }
                )

            result = pd.DataFrame(orientations)

            # Store if requested
            if store_as is not None and not result.empty:
                self.database.add_point_table(store_as, result)
                logger.info(
                    f"Stored {len(result)} contact orientations as point table '{store_as}'"
                )

            return result

        finally:
            # Clean up temporary table
            if temp_table_name in self.database.points:
                del self.database.points[temp_table_name]
