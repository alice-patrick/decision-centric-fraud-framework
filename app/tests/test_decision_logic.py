import pandas as pd
import pytest

from app.services.decision_service import (
    apply_ranking,
    assign_severity_by_percentile,
    run_static,
    run_decision_system,
)


def sample_transactions():
    return pd.DataFrame(
        {
            "transaction_id": [1, 2, 3, 4],
            "step": [1, 1, 1, 1],
            "type": [
                "TRANSFER",
                "CASH_OUT",
                "PAYMENT",
                "TRANSFER",
            ],
            "amount": [1000, 5000, 100, 20000],
            "fraud_score": [0.9, 0.4, 0.2, 0.7],
            "isFraud": [1, 0, 0, 1],
        }
    )


def test_static_threshold_flags_correct_transactions():
    df = sample_transactions()

    result = run_static(
        df=df,
        threshold=0.5,
        investigation_cost=10,
    )

    assert "alert" in result.columns
    assert result["alert"].tolist() == [1, 0, 0, 1]


def test_score_ranking_uses_fraud_score():
    df = sample_transactions()

    result = apply_ranking(
        df=df,
        policy="score",
        investigation_cost=10,
    )

    assert "rank_score" in result.columns

    assert result["rank_score"].tolist() == (
        result["fraud_score"].tolist()
    )


def test_benefit_ranking_calculates_expected_values_correctly():
    df = sample_transactions()

    result = apply_ranking(
        df=df,
        policy="benefit",
        investigation_cost=10,
    )

    expected_fraud_loss = (
        result["fraud_score"]
        * result["amount"]
    )

    expected_investigation_cost = (
        (1 - result["fraud_score"])
        * 10
    )

    expected_benefit = (
        expected_fraud_loss
        - expected_investigation_cost
    )

    assert "expected_fraud_loss" in result.columns
    assert "expected_investigation_cost" in result.columns
    assert "expected_benefit" in result.columns
    assert "rank_score" in result.columns

    assert result["expected_fraud_loss"].tolist() == pytest.approx(
        expected_fraud_loss.tolist()
    )

    assert result["expected_investigation_cost"].tolist() == pytest.approx(
        expected_investigation_cost.tolist()
    )

    assert result["expected_benefit"].tolist() == pytest.approx(
        expected_benefit.tolist()
    )

    assert result["rank_score"].tolist() == pytest.approx(
        expected_benefit.tolist()
    )


def test_false_negative_factor_changes_expected_fraud_loss():
    df = sample_transactions()

    result = apply_ranking(
        df=df,
        policy="benefit",
        investigation_cost=10,
        false_negative_factor=2.0,
    )

    expected_fraud_loss = (
        result["fraud_score"]
        * result["amount"]
        * 2.0
    )

    assert result["expected_fraud_loss"].tolist() == pytest.approx(
        expected_fraud_loss.tolist()
    )


def test_risk_zone_uses_expected_benefit_as_rank_score():
    df = sample_transactions()

    result = apply_ranking(
        df=df,
        policy="risk_zone",
        investigation_cost=10,
    )

    assert result["rank_score"].tolist() == pytest.approx(
        result["expected_benefit"].tolist()
    )


def test_risk_zone_policy_respects_floor_and_budget():
    df = sample_transactions()

    alert_budget = 3
    risk_zone_floor = 0.3

    result = run_decision_system(
        df=df,
        investigation_cost=10,
        alert_budget=alert_budget,
        policy="risk_zone",
        risk_zone_floor=risk_zone_floor,
    )

    selected = result[
        result["alert"] == 1
    ]

    assert len(selected) <= alert_budget

    assert (
        selected["fraud_score"]
        >= risk_zone_floor
    ).all()

    assert (
        selected["expected_benefit"] > 0
    ).all()


def test_zero_alert_budget_selects_no_transactions():
    df = sample_transactions()

    result = run_decision_system(
        df=df,
        investigation_cost=10,
        alert_budget=0,
        policy="risk_zone",
        risk_zone_floor=0.3,
    )

    assert int(result["alert"].sum()) == 0


def test_non_risk_zone_policy_selects_highest_ranked_transactions():
    df = sample_transactions()

    result = run_decision_system(
        df=df,
        investigation_cost=10,
        alert_budget=2,
        policy="score",
    )

    selected = result[
        result["alert"] == 1
    ].sort_values(
        "fraud_score",
        ascending=False,
    )

    assert len(selected) == 2

    assert selected["transaction_id"].tolist() == [1, 4]


def test_invalid_policy_raises_value_error():
    df = sample_transactions()

    with pytest.raises(ValueError):
        apply_ranking(
            df=df,
            policy="invalid_policy",
            investigation_cost=10,
        )


def test_negative_investigation_cost_raises_value_error():
    df = sample_transactions()

    with pytest.raises(ValueError):
        apply_ranking(
            df=df,
            policy="score",
            investigation_cost=-1,
        )


def test_invalid_false_negative_factor_raises_value_error():
    df = sample_transactions()

    with pytest.raises(ValueError):
        apply_ranking(
            df=df,
            policy="benefit",
            investigation_cost=10,
            false_negative_factor=0,
        )


def test_negative_alert_budget_raises_value_error():
    df = sample_transactions()

    with pytest.raises(ValueError):
        run_decision_system(
            df=df,
            investigation_cost=10,
            alert_budget=-1,
            policy="risk_zone",
        )


@pytest.mark.parametrize(
    "risk_zone_floor",
    [-0.1, 1.1],
)
def test_invalid_risk_zone_floor_raises_value_error(
    risk_zone_floor,
):
    df = sample_transactions()

    with pytest.raises(ValueError):
        run_decision_system(
            df=df,
            investigation_cost=10,
            alert_budget=2,
            policy="risk_zone",
            risk_zone_floor=risk_zone_floor,
        )


def test_non_alert_transactions_receive_none_severity():
    df = sample_transactions()

    result = run_static(
        df=df,
        threshold=0.95,
        investigation_cost=10,
    )

    assert (
        result.loc[
            result["alert"] == 0,
            "severity",
        ]
        == "NONE"
    ).all()


def test_alert_severity_values_are_valid():
    df = sample_transactions()

    result = run_static(
        df=df,
        threshold=0.0,
        investigation_cost=10,
    )

    valid_severities = {
        "CRITICAL",
        "HIGH",
        "MEDIUM",
        "LOW",
    }

    observed = set(
        result.loc[
            result["alert"] == 1,
            "severity",
        ]
    )

    assert observed.issubset(
        valid_severities
    )