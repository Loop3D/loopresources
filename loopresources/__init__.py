"""LoopResources package public API and constants."""

PRIVATE_DEPTH = "__lr__depth__"

from .drillhole import desurvey, DhConfig, DrillholeDatabase

from importlib.metadata import version

__version__ = version("loopresources")
# from .IO import add_points_to_geoh5
