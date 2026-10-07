"""LagScope: lagged influence between daily sentiment series."""

from lagscope.core import AnalysisResult, run
from lagscope.io import InputError, load_series
from lagscope.spec import ModelSpec

__all__ = ["AnalysisResult", "InputError", "ModelSpec", "load_series", "run"]
__version__ = "0.1.0"
