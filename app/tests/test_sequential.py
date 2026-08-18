import pandas as pd
import pytest

from app.simulation.sequential import (
    run_sequential_simulation,
    evaluate_sequential_results,
    build_operational_step_breakdown,
)


def sample_sequential_transactions():
    return pd.DataFrame(
        {
            "step": [2, 1, 1, 2, 3],
            "transaction_id": ["5", "1", "2", "4", "3"],
            "simulation_entity_key": [
                "A",
                "A",
                "B",
                "C",
                "A",
            ],
            "amount": [
                5000,
                1000,
                2000,
                3000,
                4000,
            ],
            "fraud_score": [
                0.80,
                0.90,
                0.70,
                0.60,
                0.95,
            ],
            "rank_score": [
                80.0,
                100.0,
                90.0,
                70.0,
                110.0,
            ],
            "isFraud": [
                0,
                1,
                0,
                1,
                1,
            ],
            "policy_alert_candidate": [
                True,
                True,
                True,
                True,
                True,
            ],
        }
    )


def test_sequential_output_is_chronologically_sorted():
    df = sample_sequential_transactions()

    result = run_sequential_simulation(
        alerts_df=df,
        alert_budget_per_step=2,
        suppression_window=0,
    )

    steps = result["step"].tolist()

    assert steps == sorted(steps)


def test_higher_ranked_alert_is_prioritised_within_step():
    df = pd.DataFrame(
        {
            "step": [1, 1, 1],
            "transaction_id": ["1", "2", "3"],
            "simulation_entity_key": ["A", "B", "C"],
            "amount": [1000, 1000, 1000],
            "fraud_score": [0.60, 0.95, 0.80],
            "rank_score": [60.0, 100.0, 80.0],
            "isFraud": [0, 1, 0],
            "policy_alert_candidate": [True, True, True],
        }
    )

    result = run_sequential_simulation(
        alerts_df=df,
        alert_budget_per_step=1,
        suppression_window=0,
    )

    selected = result[
        result["selected_alert"]
    ]

    assert len(selected) == 1
    assert selected.iloc[0]["transaction_id"] == "2"


def test_capacity_is_applied_per_step():
    df = pd.DataFrame(
        {
            "step": [1, 1, 1],
            "transaction_id": ["1", "2", "3"],
            "simulation_entity_key": ["A", "B", "C"],
            "amount": [1000, 2000, 3000],
            "fraud_score": [0.9, 0.8, 0.7],
            "rank_score": [100.0, 90.0, 80.0],
            "isFraud": [1, 0, 0],
            "policy_alert_candidate": [True, True, True],
        }
    )

    result = run_sequential_simulation(
        alerts_df=df,
        alert_budget_per_step=2,
        suppression_window=0,
    )

    assert int(
        result["selected_alert"].sum()
    ) == 2

    assert int(
        result["capacity_rejected"].sum()
    ) == 1


def test_repeated_entity_is_suppressed_within_window():
    df = pd.DataFrame(
        {
            "step": [1, 2],
            "transaction_id": ["1", "2"],
            "simulation_entity_key": ["A", "A"],
            "amount": [1000, 2000],
            "fraud_score": [0.9, 0.95],
            "rank_score": [100.0, 110.0],
            "isFraud": [1, 1],
            "policy_alert_candidate": [True, True],
        }
    )

    result = run_sequential_simulation(
        alerts_df=df,
        alert_budget_per_step=5,
        suppression_window=2,
    )

    first = result[
        result["transaction_id"] == "1"
    ].iloc[0]

    second = result[
        result["transaction_id"] == "2"
    ].iloc[0]

    assert bool(first["selected_alert"]) is True
    assert bool(second["suppression_applied"]) is True
    assert second["sequential_decision"] == "suppressed"


def test_repeated_entity_is_allowed_outside_suppression_window():
    df = pd.DataFrame(
        {
            "step": [1, 5],
            "transaction_id": ["1", "2"],
            "simulation_entity_key": ["A", "A"],
            "amount": [1000, 2000],
            "fraud_score": [0.9, 0.95],
            "rank_score": [100.0, 110.0],
            "isFraud": [1, 1],
            "policy_alert_candidate": [True, True],
        }
    )

    result = run_sequential_simulation(
        alerts_df=df,
        alert_budget_per_step=5,
        suppression_window=2,
    )

    assert int(
        result["selected_alert"].sum()
    ) == 2

    assert int(
        result["suppression_applied"].sum()
    ) == 0


def test_suppression_happens_before_capacity_rejection():
    df = pd.DataFrame(
        {
            "step": [1, 2, 2],
            "transaction_id": ["1", "2", "3"],
            "simulation_entity_key": ["A", "A", "B"],
            "amount": [1000, 2000, 3000],
            "fraud_score": [0.9, 0.99, 0.8],
            "rank_score": [100.0, 120.0, 90.0],
            "isFraud": [1, 1, 0],
            "policy_alert_candidate": [True, True, True],
        }
    )

    result = run_sequential_simulation(
        alerts_df=df,
        alert_budget_per_step=1,
        suppression_window=2,
    )

    repeated = result[
        result["transaction_id"] == "2"
    ].iloc[0]

    other = result[
        result["transaction_id"] == "3"
    ].iloc[0]

    assert bool(
        repeated["suppression_applied"]
    ) is True

    assert bool(
        repeated["capacity_rejected"]
    ) is False

    assert bool(
        other["selected_alert"]
    ) is True


def test_sequential_accounting_identity_holds():
    df = sample_sequential_transactions()

    result = run_sequential_simulation(
        alerts_df=df,
        alert_budget_per_step=1,
        suppression_window=2,
    )

    summary = evaluate_sequential_results(
        df=result,
        investigation_cost_per_alert=10,
        false_negative_factor=1.0,
    )

    candidates = summary[
        "policy_candidate_alerts"
    ]

    accounted = (
        summary["selected_alerts"]
        + summary["suppressed_alerts"]
        + summary["capacity_rejected_alerts"]
    )

    assert candidates == accounted


def test_investigation_cost_matches_selected_alerts():
    df = sample_sequential_transactions()

    result = run_sequential_simulation(
        alerts_df=df,
        alert_budget_per_step=1,
        suppression_window=0,
    )

    summary = evaluate_sequential_results(
        df=result,
        investigation_cost_per_alert=10,
        false_negative_factor=1.0,
    )

    expected_cost = (
        summary["selected_alerts"] * 10
    )

    assert (
        summary["investigation_cost_total"]
        == pytest.approx(expected_cost)
    )


def test_total_operational_cost_is_consistent():
    df = sample_sequential_transactions()

    result = run_sequential_simulation(
        alerts_df=df,
        alert_budget_per_step=1,
        suppression_window=0,
    )

    summary = evaluate_sequential_results(
        df=result,
        investigation_cost_per_alert=10,
        false_negative_factor=1.0,
    )

    expected_total = (
        summary["investigation_cost_total"]
        + summary["missed_fraud_cost"]
    )

    assert (
        summary["total_operational_cost"]
        == pytest.approx(expected_total)
    )


def test_operational_step_breakdown_matches_capacity():
    df = sample_sequential_transactions()

    result = run_sequential_simulation(
        alerts_df=df,
        alert_budget_per_step=1,
        suppression_window=0,
    )

    breakdown = build_operational_step_breakdown(
        df=result,
        alert_budget_per_step=1,
    )

    assert (
        breakdown["investigated_alerts"] <= 1
    ).all()

    assert (
        breakdown["unused_capacity"] >= 0
    ).all()


def test_invalid_capacity_raises_value_error():
    df = sample_sequential_transactions()

    with pytest.raises(ValueError):
        run_sequential_simulation(
            alerts_df=df,
            alert_budget_per_step=0,
            suppression_window=0,
        )


def test_negative_suppression_window_raises_value_error():
    df = sample_sequential_transactions()

    with pytest.raises(ValueError):
        run_sequential_simulation(
            alerts_df=df,
            alert_budget_per_step=1,
            suppression_window=-1,
        )