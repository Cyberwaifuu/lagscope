from pathlib import Path

import pandas as pd
import pytest

from lagscope import load_series

ROOT = Path(__file__).resolve().parents[1]
FIXTURE = ROOT / "data" / "synthetic_274.csv"


@pytest.fixture(scope="session")
def fixture_path() -> Path:
    return FIXTURE


@pytest.fixture(scope="session")
def frame() -> pd.DataFrame:
    return load_series(FIXTURE)


@pytest.fixture
def raw() -> pd.DataFrame:
    return pd.read_csv(FIXTURE, dtype=str)
