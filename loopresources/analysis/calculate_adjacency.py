"""Adjacency utilities for geological analysis."""

import numpy as np
import pandas as pd
from sklearn.neighbors import BallTree


def calculate_adjacency_ball_tree(data: pd.DataFrame, radius: float, col: str, k=5) -> np.ndarray:
    """Calculate the adjacency matrix using a BallTree."""
    locations = data[["x", "y", "z", col]].to_numpy()
    tree = BallTree(locations[:, 0:3], leaf_size=40)
    dist, ind = tree.query(locations[:, 0:3], k=k)
    adjacency_matrix = np.zeros((len(np.unique(locations[:, 3])), len(np.unique(locations[:, 3]))))
    neighbour_id = locations[ind, 3]
    for i in range(len(np.unique(locations[:, 3]))):
        for j in range(len(np.unique(locations[:, 3]))):
            if i == j:
                continue
            adjacency_matrix[i, j] = np.sum(neighbour_id[locations[:, 3] == i, :] == j)
    return adjacency_matrix


def calculate_adjacency_down_hole(
    desurveyed_drillholes: pd.DataFrame, col: str, holeid: str
) -> np.ndarray:
    """Calculate the adjacency matrix for downhole data."""
    locations = desurveyed_drillholes[["x", "y", "z", col, holeid]].to_numpy()
    holes = np.unique(locations[:, 4])
    adjacency_matrix = np.zeros((len(np.unique(locations[:, 3])), len(np.unique(locations[:, 3]))))
    mask = np.array([0, 1], dtype=int)
    for h in holes:
        hole = locations[locations[:, 4] == h]
        index = np.arange(hole.shape[0] - 1, dtype=int)
        lith_id = hole[index[:, None] + mask[None, :], 3]
        for lid1 in np.unique(lith_id):
            for lid2 in np.unique(lith_id):
                if lid1 == lid2:
                    continue
                adjacency_matrix[int(lid1), int(lid2)] += np.sum(
                    (lith_id[:, 0] == lid1) & (lith_id[:, 1] == lid2)
                )

    return adjacency_matrix
