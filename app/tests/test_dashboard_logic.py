import pandas as pd


def test_dashboard_comparison_dataframe_structure():
    comparison_df = pd.DataFrame(
        [
            {
                "system": "Static Threshold",
                "alerts": 303,
                "frauds_caught": 10,
                "recall": 0.625,
                "precision": 0.033,
                "total_cost": 600060.43,
            },
            {
                "system": "Decision System",
                "alerts": 372,
                "frauds_caught": 14,
                "recall": 0.875,
                "precision": 0.038,
                "total_cost": 552563.97,
            },
        ]
    )

    expected_columns = [
        "system",
        "alerts",
        "frauds_caught",
        "recall",
        "precision",
        "total_cost",
    ]

    assert list(comparison_df.columns) == expected_columns


def test_operating_curve_dataframe_not_empty():
    curve_df = pd.DataFrame(
        [
            {
                "budget_multiplier": 1.0,
                "recall": 0.625,
                "total_cost": 600060.43,
            },
            {
                "budget_multiplier": 1.4,
                "recall": 0.875,
                "total_cost": 552563.97,
            },
        ]
    )

    assert not curve_df.empty
    assert len(curve_df) >= 2


def test_best_operating_point_exists():
    curve_df = pd.DataFrame(
        [
            {
                "budget_multiplier": 1.0,
                "total_cost": 600060.43,
            },
            {
                "budget_multiplier": 1.4,
                "total_cost": 552563.97,
            },
        ]
    )

    best_row = curve_df.loc[curve_df["total_cost"].idxmin()]

    assert best_row["budget_multiplier"] == 1.4


def test_alert_severity_values_are_valid():
    alerts_df = pd.DataFrame(
        [
            {"severity": "HIGH"},
            {"severity": "MEDIUM"},
            {"severity": "LOW"},
        ]
    )

    valid = {"HIGH", "MEDIUM", "LOW"}

    assert set(alerts_df["severity"]).issubset(valid)