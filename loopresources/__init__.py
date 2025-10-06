"""LoopResources package public API and constants."""

PRIVATE_DEPTH = "__lr__depth__"

from .drillhole import desurvey, DhConfig, DrillholeDatabase
from .version import __version__
# from .IO import add_points_to_geoh5
