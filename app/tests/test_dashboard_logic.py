import pandas as pd

from app.dashboard.logic import (
    get_summary,
    i,
    n,
    normalise_windows,
    optional_i,
    trend_label,
)


def test_n_returns_float_for_numeric_value():
    assert n("3.5") == 3.5


def test_n_returns_default_for_none():
    assert n(None, default=7.0) == 7.0


def test_n_returns_default_for_invalid_value():
    assert n("invalid", default=2.0) == 2.0


def test_i_rounds_numeric_value():
    assert i(3.6) == 4


def test_optional_i_returns_none_for_none():
    assert optional_i(None) is None


def test_optional_i_returns_integer_for_numeric_value():
    assert optional_i("4.4") == 4


def test_get_summary_returns_requested_summary():
    payload = {
        "adaptive_sequential": {
            "summary": {
                "recall": 0.9,
                "selected_alerts": 25,
            }
        }
    }

    result = get_summary(
        payload,
        "adaptive_sequential",
    )

    assert result["recall"] == 0.9
    assert result["selected_alerts"] == 25


def test_get_summary_returns_empty_dict_when_missing():
    result = get_summary(
        {},
        "missing_key",
    )

    assert result == {}


def test_normalise_windows_renames_expected_columns():
    frame = pd.DataFrame(
        [
            {
                "monitoring_window": 2,
                "selected_alerts": 10,
                "suppressed_alerts": 3,
                "capacity_rejected_alerts": 4,
                "policy_candidate_alerts": 17,
                "total_operational_cost": 1200.0,
            }
        ]
    )

    result = normalise_windows(frame)

    expected_columns = {
        "window",
        "accepted_alerts",
        "suppressed",
        "capacity_rejected",
        "candidate_alerts",
        "operational_cost",
    }

    assert expected_columns.issubset(
        result.columns
    )


def test_normalise_windows_sorts_by_window():
    frame = pd.DataFrame(
        [
            {
                "monitoring_window": 3,
                "selected_alerts": 5,
            },
            {
                "monitoring_window": 1,
                "selected_alerts": 7,
            },
            {
                "monitoring_window": 2,
                "selected_alerts": 6,
            },
        ]
    )

    result = normalise_windows(frame)

    assert result["window"].tolist() == [
        1,
        2,
        3,
    ]


def test_normalise_windows_preserves_empty_dataframe():
    frame = pd.DataFrame()

    result = normalise_windows(frame)

    assert result.empty


def test_trend_label_returns_insufficient_data():
    series = pd.Series([1.0])

    assert (
        trend_label(series)
        == "Insufficient data"
    )


def test_trend_label_returns_stable():
    series = pd.Series(
        [100, 102, 99, 101]
    )

    assert (
        trend_label(series)
        == "Stable"
    )


def test_trend_label_returns_generally_increasing():
    series = pd.Series(
        [10, 12, 15, 20]
    )

    assert (
        trend_label(series)
        == "Generally increasing"
    )


def test_trend_label_returns_generally_decreasing():
    series = pd.Series(
        [20, 15, 12, 10]
    )

    assert (
        trend_label(series)
        == "Generally decreasing"
    )


def test_trend_label_returns_variable():
    series = pd.Series(
        [10, 20, 8, 11]
    )

    assert (
        trend_label(series)
        == "Variable"
    )


def test_trend_label_handles_non_numeric_values():
    series = pd.Series(
        ["bad", 10, None, 12]
    )

    result = trend_label(series)

    assert result in {
        "Stable",
        "Generally increasing",
        "Generally decreasing",
        "Variable",
    }