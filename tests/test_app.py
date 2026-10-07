from pathlib import Path

from streamlit.testing.v1 import AppTest

APP = str(Path(__file__).resolve().parents[1] / "app.py")


def test_app_starts_without_data():
    app = AppTest.from_file(APP, default_timeout=60).run()
    assert not app.exception
    assert "Upload a CSV" in app.info[0].value


def test_app_runs_the_example():
    app = AppTest.from_file(APP, default_timeout=60).run()
    app.toggle[0].set_value(True).run()
    assert not app.exception
    assert [metric.value for metric in app.metric][:2] == ["3 days", "1 day"]
    assert list(app.dataframe[0].value["term"]) == ["const", "s_gov_lag3", "s_blog_lag1"]
    assert [button.label for button in app.get("download_button")] == ["Download table (CSV)", "Download chart (PNG)"]


def test_app_with_hac_and_no_diagnostics():
    app = AppTest.from_file(APP, default_timeout=60).run()
    app.toggle[0].set_value(True).run()
    app.radio[0].set_value("HAC").run()
    app.multiselect[0].set_value([]).run()
    assert not app.exception
    assert len(app.expander) == 0


def test_app_accepts_an_uploaded_file():
    content = (Path(APP).parent / "data" / "synthetic_274.csv").read_bytes()
    app = AppTest.from_file(APP, default_timeout=60).run()
    app.file_uploader[0].upload("series.csv", content, "text/csv").run()
    assert not app.exception
    assert [metric.value for metric in app.metric][:2] == ["3 days", "1 day"]


def test_app_shows_a_plain_error_for_a_bad_file():
    app = AppTest.from_file(APP, default_timeout=60).run()
    app.file_uploader[0].upload("bad.csv", b"date,s_gov,s_blog\n2025-12-01,0.1,0.2\n", "text/csv").run()
    assert not app.exception
    assert "no column named 's_mass'" in app.error[0].value


def test_app_shows_a_plain_error_when_the_analysis_fails(monkeypatch):
    def failing_run(frame, spec=None):
        raise ValueError("the series cannot be analysed")

    monkeypatch.setattr("lagscope.run", failing_run)
    app = AppTest.from_file(APP, default_timeout=60).run()
    app.slider[0].set_value(3).run()
    app.toggle[0].set_value(True).run()
    assert not app.exception
    assert "could not be completed" in app.error[0].value


def test_app_shows_short_p_values():
    app = AppTest.from_file(APP, default_timeout=60).run()
    app.toggle[0].set_value(True).run()
    assert not app.exception
    assert list(app.dataframe[0].value["p_value"]) == ["< 0.0001"] * 3


def test_criterion_changes_the_value_not_the_lags():
    app = AppTest.from_file(APP, default_timeout=60).run()
    app.toggle[0].set_value(True).run()
    before = [metric.value for metric in app.metric]
    app.selectbox[0].set_value("bic").run()
    after = [metric.value for metric in app.metric]
    assert not app.exception
    assert after[:3] == before[:3]
    assert after[3] != before[3]
