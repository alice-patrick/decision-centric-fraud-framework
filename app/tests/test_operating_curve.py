import pandas as pd
import pytest

from app.services.decision_service import run_static
from app.services.metrics_service import evaluate
from app.services.operating_curve_service import (
    DEFAULT_BUDGET_MULTIPLIERS,
    build_operating_curve,
    calculate_alert_budget,
    validate_budget_multipliers,
)


def sample_transactions():
    return pd.DataFrame(
        {
            "transaction_id": [1, 2, 3, 4, 5, 6],
            "step": [1, 1, 1, 1, 1, 1],
            "type": [
                "TRANSFER",
                "CASH_OUT",
                "PAYMENT",
                "TRANSFER",
                "CASH_OUT",
                "PAYMENT",
            ],
            "amount": [
                1000,
                5000,
                100,
                20000,
                8000,
                300,
            ],
            "fraud_score": [
                0.95,
                0.80,
                0.10,
                0.70,
                0.40,
                0.20,
            ],
            "isFraud": [
                1,
                1,
                0,
                1,
                0,
                0,
            ],
        }
    )


def build_static_baseline(
    df,
    threshold=0.5,
    investigation_cost=10,
):
    static_df = run_static(
        df=df,
        threshold=threshold,
        investigation_cost=investigation_cost,
    )

    static_alerts = int(
        static_df["alert"].sum()
    )

    static_metrics = evaluate(
        df=static_df,
        alert_col="alert",
        investigation_cost=investigation_cost,
    )

    return static_alerts, static_metrics


def test_default_budget_multipliers_are_increasing():
    multipliers = list(
        DEFAULT_BUDGET_MULTIPLIERS
    )

    assert multipliers == sorted(
        multipliers
    )


def test_validate_budget_multipliers_accepts_valid_values():
    validate_budget_multipliers(
        [1.0, 1.2, 1.4]
    )


def test_empty_budget_multiplier_list_raises_value_error():
    with pytest.raises(ValueError):
        validate_budget_multipliers([])


def test_negative_budget_multiplier_raises_value_error():
    with pytest.raises(ValueError):
        validate_budget_multipliers(
            [1.0, -0.5, 1.4]
        )


def test_calculate_alert_budget():
    result = calculate_alert_budget(
        static_alerts=100,
        budget_multiplier=1.4,
    )

    assert result == 140


def test_calculate_alert_budget_uses_integer_truncation():
    result = calculate_alert_budget(
        static_alerts=3,
        budget_multiplier=1.5,
    )

    assert result == 4


def test_negative_static_alerts_raise_value_error():
    with pytest.raises(ValueError):
        calculate_alert_budget(
            static_alerts=-1,
            budget_multiplier=1.0,
        )


def test_negative_budget_multiplier_in_budget_calculation_raises():
    with pytest.raises(ValueError):
        calculate_alert_budget(
            static_alerts=10,
            budget_multiplier=-1.0,
        )


def test_operating_curve_returns_one_row_per_multiplier():
    df = sample_transactions()

    static_alerts, static_metrics = (
        build_static_baseline(df)
    )

    multipliers = [
        1.0,
        1.2,
        1.4,
    ]

    curve = build_operating_curve(
        df=df,
        static_metrics=static_metrics,
        static_alerts=static_alerts,
        investigation_cost=10,
        ranking_policy="risk_zone",
        risk_zone_floor=0.3,
        budget_multipliers=multipliers,
    )

    assert len(curve) == len(
        multipliers
    )


def test_operating_curve_contains_expected_fields():
    df = sample_transactions()

    static_alerts, static_metrics = (
        build_static_baseline(df)
    )

    curve = build_operating_curve(
        df=df,
        static_metrics=static_metrics,
        static_alerts=static_alerts,
        investigation_cost=10,
        ranking_policy="risk_zone",
        risk_zone_floor=0.3,
        budget_multipliers=[1.0],
    )

    row = curve[0]

    expected_fields = {
        "budget_multiplier",
        "alert_budget",
        "alerts",
        "frauds_caught",
        "missed_frauds",
        "false_positives",
        "recall",
        "precision",
        "alert_rate",
        "missed_fraud_cost",
        "fraud_loss_prevented",
        "investigation_cost_total",
        "total_operational_cost",
        "queue_efficiency",
        "false_positive_rate_in_queue",
        "frauds_per_100_alerts",
        "cost_per_fraud_caught",
        "operational_cost_per_transaction",
        "additional_alerts_vs_static",
        "additional_frauds_caught_vs_static",
        "cost_reduction_vs_static",
        "cost_reduction_pct_vs_static",
        "marginal_alerts",
        "marginal_frauds_caught",
        "marginal_frauds_per_100_alerts",
        "cost_diff_vs_static",
        "recall_diff_vs_static",
        "precision_diff_vs_static",
    }

    assert expected_fields.issubset(
        row.keys()
    )


def test_alert_budget_does_not_decrease():
    df = sample_transactions()

    static_alerts, static_metrics = (
        build_static_baseline(df)
    )

    curve = build_operating_curve(
        df=df,
        static_metrics=static_metrics,
        static_alerts=static_alerts,
        investigation_cost=10,
        ranking_policy="risk_zone",
        risk_zone_floor=0.3,
        budget_multipliers=[
            1.0,
            1.2,
            1.4,
        ],
    )

    budgets = [
        row["alert_budget"]
        for row in curve
    ]

    assert budgets == sorted(
        budgets
    )


def test_selected_alerts_do_not_decrease_with_budget():
    df = sample_transactions()

    static_alerts, static_metrics = (
        build_static_baseline(df)
    )

    curve = build_operating_curve(
        df=df,
        static_metrics=static_metrics,
        static_alerts=static_alerts,
        investigation_cost=10,
        ranking_policy="risk_zone",
        risk_zone_floor=0.3,
        budget_multipliers=[
            1.0,
            1.2,
            1.4,
            1.6,
        ],
    )

    alerts = [
        row["alerts"]
        for row in curve
    ]

    assert alerts == sorted(
        alerts
    )


def test_frauds_caught_do_not_decrease_with_budget():
    df = sample_transactions()

    static_alerts, static_metrics = (
        build_static_baseline(df)
    )

    curve = build_operating_curve(
        df=df,
        static_metrics=static_metrics,
        static_alerts=static_alerts,
        investigation_cost=10,
        ranking_policy="risk_zone",
        risk_zone_floor=0.3,
        budget_multipliers=[
            1.0,
            1.2,
            1.4,
            1.6,
        ],
    )

    frauds_caught = [
        row["frauds_caught"]
        for row in curve
    ]

    assert frauds_caught == sorted(
        frauds_caught
    )


def test_recall_is_valid_probability():
    df = sample_transactions()

    static_alerts, static_metrics = (
        build_static_baseline(df)
    )

    curve = build_operating_curve(
        df=df,
        static_metrics=static_metrics,
        static_alerts=static_alerts,
        investigation_cost=10,
        ranking_policy="risk_zone",
        risk_zone_floor=0.3,
    )

    for row in curve:
        assert 0 <= row["recall"] <= 1


def test_precision_is_valid_probability():
    df = sample_transactions()

    static_alerts, static_metrics = (
        build_static_baseline(df)
    )

    curve = build_operating_curve(
        df=df,
        static_metrics=static_metrics,
        static_alerts=static_alerts,
        investigation_cost=10,
        ranking_policy="risk_zone",
        risk_zone_floor=0.3,
    )

    for row in curve:
        assert 0 <= row["precision"] <= 1


def test_alert_rate_is_valid_probability():
    df = sample_transactions()

    static_alerts, static_metrics = (
        build_static_baseline(df)
    )

    curve = build_operating_curve(
        df=df,
        static_metrics=static_metrics,
        static_alerts=static_alerts,
        investigation_cost=10,
        ranking_policy="risk_zone",
        risk_zone_floor=0.3,
    )

    for row in curve:
        assert 0 <= row["alert_rate"] <= 1


def test_cost_difference_matches_operational_costs():
    df = sample_transactions()

    static_alerts, static_metrics = (
        build_static_baseline(df)
    )

    curve = build_operating_curve(
        df=df,
        static_metrics=static_metrics,
        static_alerts=static_alerts,
        investigation_cost=10,
        ranking_policy="risk_zone",
        risk_zone_floor=0.3,
        budget_multipliers=[1.0],
    )

    row = curve[0]

    expected_difference = (
        row["total_operational_cost"]
        - static_metrics[
            "total_operational_cost"
        ]
    )

    assert row[
        "cost_diff_vs_static"
    ] == pytest.approx(
        expected_difference
    )


def test_recall_difference_matches_static_baseline():
    df = sample_transactions()

    static_alerts, static_metrics = (
        build_static_baseline(df)
    )

    curve = build_operating_curve(
        df=df,
        static_metrics=static_metrics,
        static_alerts=static_alerts,
        investigation_cost=10,
        ranking_policy="risk_zone",
        risk_zone_floor=0.3,
        budget_multipliers=[1.0],
    )

    row = curve[0]

    expected_difference = (
        row["recall"]
        - static_metrics["recall"]
    )

    assert row[
        "recall_diff_vs_static"
    ] == pytest.approx(
        expected_difference
    )


def test_marginal_alerts_are_consistent():
    df = sample_transactions()

    static_alerts, static_metrics = (
        build_static_baseline(df)
    )

    curve = build_operating_curve(
        df=df,
        static_metrics=static_metrics,
        static_alerts=static_alerts,
        investigation_cost=10,
        ranking_policy="risk_zone",
        risk_zone_floor=0.3,
        budget_multipliers=[
            1.0,
            1.2,
            1.4,
        ],
    )

    previous_alerts = int(
        static_metrics["alerts"]
    )

    for row in curve:
        expected_marginal = (
            row["alerts"]
            - previous_alerts
        )

        assert row[
            "marginal_alerts"
        ] == expected_marginal

        previous_alerts = row[
            "alerts"
        ]