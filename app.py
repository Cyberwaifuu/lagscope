"""Streamlit interface for LagScope."""

from __future__ import annotations

import io
from pathlib import Path

import pandas as pd
import streamlit as st

from lagscope import AnalysisResult, InputError, ModelSpec, load_series, run
from lagscope.report import series_figure, summary_table, to_csv_bytes, to_png_bytes
from lagscope.spec import CRITERIA, DIAGNOSTICS

EXAMPLE = Path(__file__).parent / "data" / "synthetic_274.csv"


@st.cache_data(show_spinner=False)
def analyse(content: bytes, spec: ModelSpec) -> tuple[pd.DataFrame, AnalysisResult]:
    """Validate the uploaded bytes and run the model; cached by content and settings."""
    frame = load_series(io.BytesIO(content))
    return frame, run(frame, spec)


st.set_page_config(page_title="LagScope", layout="wide")
st.title("LagScope")
st.caption(
    "Lag and strength of influence between daily sentiment series: s_mass(t) = α + β1·s_gov(t−k1) + β2·s_blog(t−k2) + ε"
)

with st.sidebar:
    st.header("Settings")
    max_lag = st.slider("Maximum lag (days)", min_value=1, max_value=14, value=7)
    criterion = st.selectbox("Lag selection criterion", CRITERIA, format_func=str.upper)
    cov_type = st.radio(
        "Standard errors",
        ("nonrobust", "HAC"),
        format_func=lambda v: "Classical" if v == "nonrobust" else "Newey–West (HAC)",
    )
    diagnostics = st.multiselect("Diagnostics", DIAGNOSTICS, default=list(DIAGNOSTICS))

use_example = st.toggle("Use the synthetic example (274 days)")
uploaded = st.file_uploader("Daily sentiment CSV with columns date, s_gov, s_blog, s_mass", type="csv")

if use_example:
    content = EXAMPLE.read_bytes()
elif uploaded is not None:
    content = uploaded.getvalue()
else:
    st.info("Upload a CSV or switch on the synthetic example to start.")
    st.stop()

spec = ModelSpec(max_lag=max_lag, criterion=criterion, cov_type=cov_type, diagnostics=tuple(diagnostics))
try:
    frame, result = analyse(content, spec)
except InputError as error:
    st.error(str(error))
    st.stop()
except ValueError as error:
    st.error(f"The analysis could not be completed: {error}.")
    st.stop()


P_FLOOR = 0.0001


def p_text(value: float) -> str:
    """Format a p-value for display."""
    if pd.isna(value):
        return ""
    return "< 0.0001" if value < P_FLOOR else f"{value:.4f}"


def shown(table: pd.DataFrame) -> pd.DataFrame:
    """Copy of a table with p-values formatted for display."""
    return table.assign(p_value=table["p_value"].map(p_text))


def days(value: int) -> str:
    """Format a lag in days."""
    return f"{value} day" if value == 1 else f"{value} days"


left, middle, right, last = st.columns(4)
left.metric("Lag k1 (government)", days(result.lags["s_gov"]))
middle.metric("Lag k2 (bloggers)", days(result.lags["s_blog"]))
right.metric("R²", f"{result.r_squared:.3f}", help=f"{result.nobs} observations")
last.metric(
    result.criterion.upper(),
    f"{result.lag_search.iloc[0][result.criterion]:.1f}",
    help="Value of the selected criterion for the chosen lag pair; lower is better",
)
st.caption(
    f"All lag pairs are compared on the same {result.nobs} days with the same number of coefficients, "
    "so AIC, BIC and HQIC always choose the same pair. The criterion changes the value shown above, not the lags."
)

st.subheader("Coefficients")
table = summary_table(result)
st.dataframe(shown(table), hide_index=True)

st.subheader("The three series")
figure = series_figure(frame)
st.pyplot(figure)

csv_column, png_column = st.columns(2)
csv_column.download_button("Download table (CSV)", to_csv_bytes(result), "lagscope_coefficients.csv", "text/csv")
png_column.download_button("Download chart (PNG)", to_png_bytes(figure), "lagscope_series.png", "image/png")

st.subheader("Lag search: five best pairs")
st.dataframe(result.lag_search.head(5), hide_index=True)

if result.diagnostics:
    with st.expander("Diagnostics"):
        for name, diagnostic in result.diagnostics.items():
            st.markdown(f"**{name.upper()}**")
            st.dataframe(shown(diagnostic), hide_index=True)
