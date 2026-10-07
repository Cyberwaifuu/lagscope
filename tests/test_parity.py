import numpy as np

from lagscope import ModelSpec
from lagscope.core import fit
from reference.reference_ols import reference_fit

LAGS = {"s_gov": 3, "s_blog": 1}
TOLERANCE = 1e-4


def test_matches_independent_reference(frame):
    spec = ModelSpec()
    ours = fit(frame, spec, LAGS)
    theirs = reference_fit(
        frame["s_mass"].to_numpy(),
        {name: frame[name].to_numpy() for name in spec.predictors},
        LAGS,
        spec.max_lag,
    )
    assert int(ours.nobs) == theirs["nobs"]
    np.testing.assert_allclose(ours.params.to_numpy(), theirs["beta"], atol=TOLERANCE)
    np.testing.assert_allclose(ours.bse.to_numpy(), theirs["std_err"], atol=TOLERANCE)
    np.testing.assert_allclose(ours.pvalues.to_numpy(), theirs["p_value"], atol=TOLERANCE)


def test_parity_fails_on_a_wrong_coefficient(frame):
    spec = ModelSpec()
    ours = fit(frame, spec, LAGS)
    shifted = ours.params.to_numpy() + np.array([0.0, 0.0, 0.01])
    theirs = reference_fit(
        frame["s_mass"].to_numpy(),
        {name: frame[name].to_numpy() for name in spec.predictors},
        LAGS,
        spec.max_lag,
    )
    assert not np.allclose(shifted, theirs["beta"], atol=TOLERANCE)
