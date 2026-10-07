"""Lag search, OLS estimation and optional diagnostics."""

from __future__ import annotations

import itertools
from dataclasses import dataclass, field

import numpy as np
import pandas as pd
import statsmodels.api as sm
from statsmodels.regression.linear_model import RegressionResultsWrapper
from statsmodels.stats.diagnostic import acorr_ljungbox
from statsmodels.tsa.stattools import adfuller, grangercausalitytests

from lagscope.spec import ModelSpec


@dataclass
class AnalysisResult:
    """Output of one run: chosen lags, coefficient table, fit statistics and diagnostics."""

    lags: dict[str, int]
    coefficients: pd.DataFrame
    nobs: int
    r_squared: float
    criterion: str
    lag_search: pd.DataFrame
    diagnostics: dict[str, pd.DataFrame] = field(default_factory=dict)


def design(frame: pd.DataFrame, spec: ModelSpec, lags: dict[str, int]) -> tuple[pd.Series, pd.DataFrame]:
    """Build the target and lagged predictors on the common sample that starts after max_lag."""
    columns = {f"{name}_lag{lags[name]}": frame[name].shift(lags[name]) for name in spec.predictors}
    exog = sm.add_constant(pd.DataFrame(columns, index=frame.index), has_constant="add")
    endog = frame[spec.target]
    sample = frame.index[spec.max_lag :]
    return endog.loc[sample], exog.loc[sample]


def fit(frame: pd.DataFrame, spec: ModelSpec, lags: dict[str, int]) -> RegressionResultsWrapper:
    """Estimate the regression by OLS with the covariance type set in the spec."""
    endog, exog = design(frame, spec, lags)
    model = sm.OLS(endog, exog)
    if spec.cov_type == "HAC":
        return model.fit(cov_type="HAC", cov_kwds={"maxlags": spec.hac_maxlags})
    return model.fit()


def hqic(result: RegressionResultsWrapper) -> float:
    """Hannan-Quinn criterion with the same parameter count statsmodels uses for AIC and BIC."""
    k = result.df_model + result.k_constant
    return float(-2 * result.llf + 2 * k * np.log(np.log(result.nobs)))


def search_lags(frame: pd.DataFrame, spec: ModelSpec) -> tuple[dict[str, int], pd.DataFrame]:
    """Try every lag combination on the same sample and keep the one with the lowest criterion."""
    rows = []
    for combination in itertools.product(spec.lag_grid, repeat=len(spec.predictors)):
        lags = dict(zip(spec.predictors, combination, strict=True))
        result = fit(frame, spec, lags)
        rows.append(
            {
                **{f"k_{name}": lag for name, lag in lags.items()},
                "aic": result.aic,
                "bic": result.bic,
                "hqic": hqic(result),
                "nobs": int(result.nobs),
            }
        )
    table = pd.DataFrame(rows).sort_values(spec.criterion, kind="stable").reset_index(drop=True)
    best = table.iloc[0]
    return {name: int(best[f"k_{name}"]) for name in spec.predictors}, table


def coefficient_table(result: RegressionResultsWrapper) -> pd.DataFrame:
    """Coefficients with standard errors, t statistics and p-values."""
    return pd.DataFrame(
        {
            "coef": result.params,
            "std_err": result.bse,
            "t": result.tvalues,
            "p_value": result.pvalues,
        }
    ).rename_axis("term")


def adf_stage(
    frame: pd.DataFrame, spec: ModelSpec, result: RegressionResultsWrapper, lags: dict[str, int]
) -> pd.DataFrame:
    """Augmented Dickey-Fuller test for every series."""
    rows = []
    for name in (spec.target, *spec.predictors):
        statistic, p_value, *_ = adfuller(frame[name].to_numpy(), autolag="AIC", result_object=False)
        rows.append({"series": name, "adf_stat": statistic, "p_value": p_value, "stationary_at_5pct": p_value < 0.05})
    return pd.DataFrame(rows)


def granger_stage(
    frame: pd.DataFrame, spec: ModelSpec, result: RegressionResultsWrapper, lags: dict[str, int]
) -> pd.DataFrame:
    """Granger test of each predictor at its chosen lag."""
    rows = []
    for name in spec.predictors:
        lag = lags[name]
        if lag == 0:
            rows.append(
                {"cause": name, "lag": lag, "f_stat": np.nan, "p_value": np.nan, "note": "lag 0: test not applicable"}
            )
            continue
        data = frame[[spec.target, name]].to_numpy()
        test = grangercausalitytests(data, maxlag=[lag])
        f_stat, p_value, *_ = test[lag][0]["ssr_ftest"]
        rows.append({"cause": name, "lag": lag, "f_stat": f_stat, "p_value": p_value, "note": ""})
    return pd.DataFrame(rows)


def ljungbox_stage(
    frame: pd.DataFrame, spec: ModelSpec, result: RegressionResultsWrapper, lags: dict[str, int]
) -> pd.DataFrame:
    """Ljung-Box test for autocorrelation left in the residuals."""
    lag = max(1, min(10, int(result.nobs) // 5))
    table = acorr_ljungbox(result.resid, lags=[lag])
    return pd.DataFrame(
        {"lag": [lag], "lb_stat": table["lb_stat"].to_numpy(), "p_value": table["lb_pvalue"].to_numpy()}
    )


STAGES = {"adf": adf_stage, "granger": granger_stage, "ljungbox": ljungbox_stage}


def run(frame: pd.DataFrame, spec: ModelSpec | None = None) -> AnalysisResult:
    """Full pipeline: lag search, final OLS fit, then the diagnostic stages listed in the spec."""
    spec = spec or ModelSpec()
    missing = [name for name in (spec.target, *spec.predictors) if name not in frame.columns]
    if missing:
        raise ValueError(f"columns not found: {missing}")
    if len(frame) <= spec.max_lag + len(spec.predictors) + 2:
        raise ValueError("too few rows for the requested maximum lag")
    lags, search_table = search_lags(frame, spec)
    result = fit(frame, spec, lags)
    diagnostics = {name: STAGES[name](frame, spec, result, lags) for name in spec.diagnostics}
    return AnalysisResult(
        lags=lags,
        coefficients=coefficient_table(result),
        nobs=int(result.nobs),
        r_squared=float(result.rsquared),
        criterion=spec.criterion,
        lag_search=search_table,
        diagnostics=diagnostics,
    )
