import numpy as np
from scipy.interpolate import interp1d
from LoopStructural.utils import plungeazimuth2vector
def slerp(unit_vectors,  depth, newdepth):
    """Create interpolating functions for azimuth and dip.

    Parameters
    ----------
    unit_vectors : array-like
        Array of unit vectors representing the drillhole trajectory.
    depth : array-like
        Array of depth values.
    newdepth : array-like
        Array of new depth values for interpolation.

    Returns
    -------
    new_unit_vectors: array-like
        Interpolated unit vectors at new depth values.
    """
    try:

        depth = np.asarray(depth)
        newdepth = np.asarray(newdepth)
        unit_vectors = np.asarray(unit_vectors)
    except Exception as e:
        raise ValueError(
            "Input arrays could not be converted to numpy arrays."
        ) from e
    # Precompute dot products and dogleg angles
    dot_products = np.einsum('ij,ij->i', unit_vectors[:-1], unit_vectors[1:])
    dot_products = np.clip(dot_products, -1.0, 1.0)  # Clamp for acos
    dogleg_angles = np.arccos(dot_products)

    # Find segment index for each new depth
    segment_idx = np.searchsorted(depth, newdepth, side='right') - 1
    segment_idx = np.clip(
        segment_idx, 0, len(depth) - 2
    )  # ensure valid range
    # Fraction along segment
    f = (newdepth - depth[segment_idx]) / (
        depth[segment_idx + 1] - depth[segment_idx]
    )
    denominator = np.sin(dogleg_angles[segment_idx])
    denominator[denominator == 0] = 1e-6  # Prevent division by zero
    # SLERP terms
    term1 = np.sin((1 - f) * dogleg_angles[segment_idx]) / denominator
    term2 = np.sin(f * dogleg_angles[segment_idx]) / denominator

    # Handle zero dogleg (avoid division by zero)
    zero_dl_mask = dogleg_angles[segment_idx] == 0
    term1[zero_dl_mask] = 1.0
    term2[zero_dl_mask] = 0.0

    # Interpolated vectors
    new_vectors = (
        term1[:, None] * unit_vectors[segment_idx] + term2[:, None] * unit_vectors[segment_idx + 1]
    )
    return new_vectors 

def vector2trendandplunge(vectors):
    new_trend = np.arctan2(vectors[:, 1], vectors[:, 0]) % (2 * np.pi)
    new_plunge = np.arcsin(np.clip(vectors[:, 2], -1.0, 1.0))
    return new_trend, new_plunge

def trendandplunge2vector(trend, plunge):
    x = np.cos(plunge) * np.cos(trend)
    y = np.cos(plunge) * np.sin(trend)
    z = np.sin(plunge)
    return np.vstack([x, y, z]).T
