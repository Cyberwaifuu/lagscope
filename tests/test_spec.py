import pytest

from lagscope import ModelSpec


def test_defaults():
    spec = ModelSpec()
    assert spec.criterion == "aic"
    assert spec.cov_type == "nonrobust"
    assert list(spec.lag_grid) == list(range(0, 8))


@pytest.mark.parametrize(
    "kwargs",
    [
        {"criterion": "r2"},
        {"cov_type": "robust"},
        {"min_lag": 5, "max_lag": 2},
        {"max_lag": 31},
        {"predictors": ()},
        {"predictors": ("s_mass",)},
        {"diagnostics": ("kpss",)},
        {"hac_maxlags": -1},
    ],
)
def test_invalid_settings_are_rejected(kwargs):
    with pytest.raises(ValueError):
        ModelSpec(**kwargs)


def test_spec_is_hashable_for_caching():
    assert hash(ModelSpec()) == hash(ModelSpec())
