import io

import pandas as pd
import pytest

from lagscope import InputError, load_series
from lagscope.io import MESSAGES, MIN_ROWS


def to_buffer(table: pd.DataFrame) -> io.StringIO:
    return io.StringIO(table.to_csv(index=False))


def test_fixture_loads(frame):
    assert len(frame) == 274
    assert list(frame.columns) == ["s_gov", "s_blog", "s_mass"]
    assert frame.index.is_monotonic_increasing
    assert frame.index[0] == pd.Timestamp("2025-12-01")
    assert frame.index[-1] == pd.Timestamp("2026-08-31")


def test_unsorted_rows_are_sorted(raw):
    shuffled = raw.sample(frac=1, random_state=1)
    assert load_series(to_buffer(shuffled)).index.is_monotonic_increasing


def broken(raw: pd.DataFrame, case: str) -> pd.DataFrame:
    table = raw.copy()
    if case == "missing_column":
        return table.drop(columns="s_blog")
    if case == "extra_column":
        return table.assign(text="post text")
    if case == "bad_date":
        table.loc[5, "date"] = "05.12.2025"
        return table
    if case == "duplicate_date":
        table.loc[5, "date"] = table.loc[4, "date"]
        return table
    if case == "date_gap":
        return table.drop(index=10)
    if case == "missing_value":
        table.loc[7, "s_mass"] = ""
        return table
    if case == "not_numeric":
        table.loc[7, "s_gov"] = "high"
        return table
    if case == "out_of_range":
        table.loc[7, "s_blog"] = "1.5"
        return table
    if case == "too_few_rows":
        return table.head(MIN_ROWS - 1)
    if case == "constant_series":
        return table.assign(s_gov="0.1")
    raise AssertionError(case)


CASES = [
    "missing_column",
    "extra_column",
    "bad_date",
    "duplicate_date",
    "date_gap",
    "missing_value",
    "not_numeric",
    "out_of_range",
    "too_few_rows",
    "constant_series",
]

HEADER = b"date,s_gov,s_blog,s_mass\n"
UNREADABLE = {
    "empty_file": b"",
    "bad_encoding": HEADER + b"2025-12-01,0.1,0.2,\xff\n",
    "bad_structure": HEADER + b"2025-12-01,0.1,0.2,0.3\n2025-12-02,0.1,0.2,0.3,9,9\n",
    "wrong_delimiter": b"date;s_gov;s_blog;s_mass\n2025-12-01;0.1;0.2;0.3\n",
}


@pytest.mark.parametrize("case", CASES)
def test_each_rule_has_its_own_error(raw, case):
    with pytest.raises(InputError) as caught:
        load_series(to_buffer(broken(raw, case)))
    assert caught.value.code == case
    assert str(caught.value).endswith(".")


@pytest.mark.parametrize("code", sorted(UNREADABLE))
def test_unreadable_files_get_a_plain_error(code):
    with pytest.raises(InputError) as caught:
        load_series(io.BytesIO(UNREADABLE[code]))
    assert caught.value.code == code
    assert str(caught.value).endswith(".")


def test_every_error_code_is_tested():
    assert set(CASES) | set(UNREADABLE) == set(MESSAGES)


def test_extra_text_column_is_rejected(raw):
    with pytest.raises(InputError, match="extra column 'text'"):
        load_series(to_buffer(raw.assign(text="post text")))


def test_exactly_minimum_rows_is_accepted(raw):
    assert len(load_series(to_buffer(raw.head(MIN_ROWS)))) == MIN_ROWS


def test_header_only_file_is_empty():
    with pytest.raises(InputError) as caught:
        load_series(io.StringIO("date,s_gov,s_blog,s_mass\n"))
    assert caught.value.code == "empty_file"


def test_file_saved_with_a_byte_order_mark_is_accepted(fixture_path):
    assert len(load_series(io.BytesIO(b"\xef\xbb\xbf" + fixture_path.read_bytes()))) == 274


def test_short_row_is_reported_as_an_empty_cell(fixture_path):
    lines = fixture_path.read_text(encoding="utf-8").splitlines()
    lines[5] = lines[5].rsplit(",", 1)[0]
    with pytest.raises(InputError) as caught:
        load_series(io.StringIO("\n".join(lines)))
    assert caught.value.code == "missing_value"
