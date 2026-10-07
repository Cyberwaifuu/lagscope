"""Model settings in one object."""

from __future__ import annotations

from dataclasses import dataclass

CRITERIA = ("aic", "bic", "hqic")
COV_TYPES = ("nonrobust", "HAC")
DIAGNOSTICS = ("adf", "granger", "ljungbox")


@dataclass(frozen=True)
class ModelSpec:
    """Everything that defines one estimation run."""

    target: str = "s_mass"
    predictors: tuple[str, ...] = ("s_gov", "s_blog")
    min_lag: int = 0
    max_lag: int = 7
    criterion: str = "aic"
    cov_type: str = "nonrobust"
    hac_maxlags: int = 5
    diagnostics: tuple[str, ...] = DIAGNOSTICS

    def __post_init__(self) -> None:
        if self.criterion not in CRITERIA:
            raise ValueError(f"criterion must be one of {CRITERIA}, got '{self.criterion}'")
        if self.cov_type not in COV_TYPES:
            raise ValueError(f"cov_type must be one of {COV_TYPES}, got '{self.cov_type}'")
        if not 0 <= self.min_lag <= self.max_lag <= 30:
            raise ValueError("lags must satisfy 0 <= min_lag <= max_lag <= 30")
        if not self.predictors:
            raise ValueError("at least one predictor is required")
        if self.target in self.predictors:
            raise ValueError("the target cannot also be a predictor")
        unknown = [name for name in self.diagnostics if name not in DIAGNOSTICS]
        if unknown:
            raise ValueError(f"unknown diagnostics: {unknown}")
        if self.hac_maxlags < 0:
            raise ValueError("hac_maxlags must be non-negative")

    @property
    def lag_grid(self) -> range:
        """All lags tried for each predictor."""
        return range(self.min_lag, self.max_lag + 1)
