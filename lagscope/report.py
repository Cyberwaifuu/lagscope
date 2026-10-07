"""Tables, chart and export files."""

from __future__ import annotations

import io

import pandas as pd
from matplotlib.figure import Figure

from lagscope.core import AnalysisResult

LABELS = {"s_gov": "Government channels", "s_blog": "Bloggers", "s_mass": "Mass audience"}


def summary_table(result: AnalysisResult) -> pd.DataFrame:
    """Coefficient table with the chosen lag next to each predictor."""
    table = result.coefficients.reset_index()
    table["lag_days"] = [
        next((lag for name, lag in result.lags.items() if term.startswith(f"{name}_lag")), None)
        for term in table["term"]
    ]
    return table[["term", "lag_days", "coef", "std_err", "t", "p_value"]]


def to_csv_bytes(result: AnalysisResult) -> bytes:
    """Summary table as UTF-8 CSV."""
    return summary_table(result).to_csv(index=False).encode("utf-8")


def series_figure(frame: pd.DataFrame) -> Figure:
    """Line chart of the three daily series."""
    figure = Figure(figsize=(10, 4))
    axis = figure.subplots()
    for column in ("s_gov", "s_blog", "s_mass"):
        if column in frame.columns:
            axis.plot(frame.index, frame[column], label=LABELS.get(column, column), linewidth=1.2)
    axis.axhline(0, color="grey", linewidth=0.6)
    axis.set_ylim(-1.05, 1.05)
    axis.set_ylabel("Daily sentiment (-1 to 1)")
    axis.legend(loc="upper left", ncol=3, frameon=False)
    figure.tight_layout()
    return figure


def to_png_bytes(figure: Figure) -> bytes:
    """Figure as PNG at 150 dpi."""
    buffer = io.BytesIO()
    figure.savefig(buffer, format="png", dpi=150)
    return buffer.getvalue()
