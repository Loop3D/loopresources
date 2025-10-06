"""Drillhole subpackage: configuration, utilities and database helpers for drillhole data."""

from .dhconfig import DhConfig
from .dbconfig import DbConfig
from .desurvey import desurvey
from .drillhole_database import DrillholeDatabase
from .drillhole import DrillHole
from .dataframeinterpolator import DataFrameInterpolator

from .resample import resample_interval, resample_point, desurvey_point

try:
    from .orientation import alphaBeta2vector, alphaBetaGamma2vector
except ImportError:
    # LoopStructural not available, orientation functions not available
    pass
