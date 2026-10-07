import time

import numpy as np
import pytest

from lagscope import ModelSpec, run
from lagscope.core import fit, hqic, search_lags

TRUE_LAGS = {"s_gov": 3, "s_blog": 1}
TRUE_BETAS = {"s_gov_lag3": 0.25, "s_blog_lag1": 0.45}


@pytest.mark.parametrize("criterion", ["aic", "bic", "hqic"])
def test_injected_lags_are_recovered(frame, criterion):
    result = run(frame, ModelSpec(criterion=criterion, diagnostics=()))
    assert result.lags == TRUE_LAGS


def test_injected_effects_are_recovered(frame):
    result = run(frame, ModelSpec(diagnostics=()))
    for term, beta in TRUE_BETAS.items():
        assert result.coefficients.loc[term, "coef"] == pytest.approx(beta, abs=0.05)
        assert result.coefficients.loc[term, "p_value"] < 0.01


def test_all_candidates_use_the_same_sample(frame):
    spec = ModelSpec(max_lag=7, diagnostics=())
    _, table = search_lags(frame, spec)
    assert table["nobs"].nunique() == 1
    assert table["nobs"].iloc[0] == len(frame) - spec.max_lag
    assert len(table) == len(spec.lag_grid) ** 2


def test_hac_changes_errors_not_coefficients(frame):
    classical = fit(frame, ModelSpec(), TRUE_LAGS)
    hac = fit(frame, ModelSpec(cov_type="HAC"), TRUE_LAGS)
    np.testing.assert_allclose(classical.params, hac.params, atol=1e-12)
    assert not np.allclose(classical.bse, hac.bse)


def test_hqic_equals_the_statsmodels_value(frame):
    result = fit(frame, ModelSpec(), TRUE_LAGS)
    assert hqic(result) == pytest.approx(result.info_criteria("hqic"))


def test_diagnostics_are_removable(frame):
    full = run(frame, ModelSpec())
    bare = run(frame, ModelSpec(diagnostics=()))
    assert set(full.diagnostics) == {"adf", "granger", "ljungbox"}
    assert bare.diagnostics == {}
    np.testing.assert_allclose(full.coefficients.to_numpy(), bare.coefficients.to_numpy())


def test_granger_skips_lag_zero(frame):
    result = run(frame, ModelSpec(min_lag=0, max_lag=0, diagnostics=("granger",)))
    assert result.diagnostics["granger"]["note"].str.contains("not applicable").all()


def test_missing_column_is_reported(frame):
    with pytest.raises(ValueError, match="columns not found"):
        run(frame.drop(columns="s_blog"))


def test_full_run_is_under_five_seconds(frame):
    start = time.perf_counter()
    run(frame, ModelSpec())
    assert time.perf_counter() - start < 5


def test_too_few_rows_for_the_lag_range(frame):
    with pytest.raises(ValueError, match="too few rows"):
        run(frame.head(10), ModelSpec(max_lag=8))
