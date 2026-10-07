"""LagScope: lagged influence between daily sentiment series."""

from lagscope.io import InputError, load_series
from lagscope.spec import ModelSpec

__all__ = ["InputError", "ModelSpec", "load_series"]
__version__ = "0.1.0"
