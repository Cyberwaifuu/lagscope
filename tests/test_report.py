import io

import pandas as pd

from lagscope import ModelSpec, run
from lagscope.report import series_figure, summary_table, to_csv_bytes, to_png_bytes


def test_summary_table_shows_lags(frame):
    table = summary_table(run(frame, ModelSpec(diagnostics=())))
    lags = dict(zip(table["term"], table["lag_days"], strict=True))
    assert lags["s_gov_lag3"] == 3
    assert lags["s_blog_lag1"] == 1
    assert pd.isna(lags["const"])


def test_csv_export_round_trip(frame):
    result = run(frame, ModelSpec(diagnostics=()))
    exported = pd.read_csv(io.BytesIO(to_csv_bytes(result)))
    assert list(exported.columns) == ["term", "lag_days", "coef", "std_err", "t", "p_value"]
    assert len(exported) == 3


def test_png_export_is_a_png(frame):
    content = to_png_bytes(series_figure(frame))
    assert content[:8] == b"\x89PNG\r\n\x1a\n"
    assert len(content) > 10_000
