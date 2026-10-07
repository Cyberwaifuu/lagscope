"""Independent NumPy implementation of the lagged regression, used only by the parity test."""

from __future__ import annotations

import numpy as np
from scipy import stats


def reference_fit(target: np.ndarray, predictors: dict[str, np.ndarray], lags: dict[str, int], max_lag: int) -> dict:
    """OLS with classical standard errors computed directly from the normal equations."""
    n = len(target)
    rows = np.arange(max_lag, n)
    columns = [np.ones(len(rows))]
    for name, series in predictors.items():
        columns.append(series[rows - lags[name]])
    x = np.column_stack(columns)
    y = target[rows]
    xtx_inv = np.linalg.inv(x.T @ x)
    beta = xtx_inv @ x.T @ y
    residuals = y - x @ beta
    dof = len(y) - x.shape[1]
    sigma2 = residuals @ residuals / dof
    std_err = np.sqrt(np.diag(sigma2 * xtx_inv))
    t_values = beta / std_err
    p_values = 2 * stats.t.sf(np.abs(t_values), dof)
    return {"beta": beta, "std_err": std_err, "p_value": p_values, "nobs": len(y)}
