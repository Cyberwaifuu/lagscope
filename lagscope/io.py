"""Reading and validating the input CSV."""

from __future__ import annotations

from pathlib import Path
from typing import IO

import pandas as pd

REQUIRED_COLUMNS = ("date", "s_gov", "s_blog", "s_mass")
SERIES_COLUMNS = REQUIRED_COLUMNS[1:]
MIN_ROWS = 60
DELIMITERS = {";": "semicolons", "\t": "tabs"}

MESSAGES = {
    "empty_file": "The file is empty.",
    "bad_encoding": "The file is not UTF-8 text. Save it as CSV UTF-8 and upload it again.",
    "bad_structure": "The file cannot be read as a table. Every row needs exactly four values separated by commas.",
    "wrong_delimiter": "The file separates values with {value}. Save it with commas between the values.",
    "missing_column": "The file has no column named '{column}'.",
    "extra_column": "The file has an extra column '{column}'. Only date, s_gov, s_blog and s_mass are allowed.",
    "bad_date": "Row {row} has a date that cannot be read: '{value}'. Use the format YYYY-MM-DD.",
    "duplicate_date": "The date {value} appears more than once.",
    "date_gap": "Dates must be consecutive days, but {value} is missing.",
    "missing_value": "Column '{column}' has an empty cell in row {row}.",
    "not_numeric": "Column '{column}' has a value that is not a number in row {row}: '{value}'.",
    "out_of_range": "Column '{column}' has the value {value} in row {row}; values must lie between -1 and 1.",
    "too_few_rows": "The file has {value} rows; at least {minimum} are needed.",
    "constant_series": "Column '{column}' has the same value in every row, so no relation can be estimated.",
}


class InputError(ValueError):
    """Raised when the input file breaks a rule; carries a code and a plain message."""

    def __init__(self, code: str, **details: object) -> None:
        self.code = code
        self.details = details
        super().__init__(MESSAGES[code].format(minimum=MIN_ROWS, **details))


def load_series(source: str | Path | IO) -> pd.DataFrame:
    """Read a daily sentiment CSV and return it indexed by date, or raise InputError."""
    try:
        frame = pd.read_csv(source, dtype=str, keep_default_na=False, encoding="utf-8-sig").fillna("")
    except pd.errors.EmptyDataError as error:
        raise InputError("empty_file") from error
    except UnicodeDecodeError as error:
        raise InputError("bad_encoding") from error
    except pd.errors.ParserError as error:
        raise InputError("bad_structure") from error
    frame.columns = [str(column).strip() for column in frame.columns]
    if len(frame.columns) == 1:
        for delimiter, name in DELIMITERS.items():
            if delimiter in frame.columns[0]:
                raise InputError("wrong_delimiter", value=name)
    for column in REQUIRED_COLUMNS:
        if column not in frame.columns:
            raise InputError("missing_column", column=column)
    for column in frame.columns:
        if column not in REQUIRED_COLUMNS:
            raise InputError("extra_column", column=column)
    if frame.empty:
        raise InputError("empty_file")

    raw_dates = frame["date"].str.strip()
    dates = pd.to_datetime(raw_dates, format="%Y-%m-%d", errors="coerce")
    for row, value in enumerate(dates):
        if pd.isna(value):
            raise InputError("bad_date", row=row + 2, value=raw_dates.iloc[row])
    duplicated = dates[dates.duplicated()]
    if not duplicated.empty:
        raise InputError("duplicate_date", value=duplicated.iloc[0].date())
    expected = pd.date_range(dates.min(), dates.max(), freq="D")
    missing = expected.difference(pd.DatetimeIndex(dates))
    if len(missing) > 0:
        raise InputError("date_gap", value=missing[0].date())

    values = {}
    for column in SERIES_COLUMNS:
        raw = frame[column].str.strip()
        numeric = pd.to_numeric(raw, errors="coerce")
        for row in range(len(frame)):
            if raw.iloc[row] == "":
                raise InputError("missing_value", column=column, row=row + 2)
            if pd.isna(numeric.iloc[row]):
                raise InputError("not_numeric", column=column, row=row + 2, value=raw.iloc[row])
            if not -1.0 <= numeric.iloc[row] <= 1.0:
                raise InputError("out_of_range", column=column, row=row + 2, value=numeric.iloc[row])
        values[column] = numeric.to_numpy(dtype=float)

    if len(frame) < MIN_ROWS:
        raise InputError("too_few_rows", value=len(frame))
    for column in SERIES_COLUMNS:
        if len(set(values[column])) == 1:
            raise InputError("constant_series", column=column)
    result = pd.DataFrame(values, index=pd.DatetimeIndex(dates, name="date"))
    return result.sort_index()
