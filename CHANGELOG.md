# Changelog

## v0.1.0

- CSV loading with fourteen validation rules and plain-language error messages.
- Lag search over a common sample with AIC, BIC or HQIC.
- OLS estimation with classical or Newey–West (HAC) standard errors.
- Optional ADF, Granger and Ljung–Box diagnostics.
- Coefficient table, chart of the three series, CSV and PNG export.
- Streamlit interface with a synthetic example.
- CI on Ubuntu and Windows (Python 3.12, 3.13, 3.14), coverage gate at 90%, package build; release workflow on tags.
- Interface shows the value of the selected criterion, the five best lag pairs and p-values shortened for display (the CSV export keeps full precision).
