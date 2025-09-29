from abc import ABC


class Interpolator(ABC):
    """Abstract base class for all interpolators."""

    def __init__(self):
        pass

    def __call__(self, X):
        pass
