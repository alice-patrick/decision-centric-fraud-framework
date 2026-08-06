import pandas as pd
import pytest

from app.api.main import (
    apply_ranking,
    run_static,
    run_decision_system,
    assign_severity,
)


def sample_transactions():
    return pd.DataFrame(
        {
            "transaction_id": [1, 2, 3, 4],
            "step": [1, 1, 1, 1],
            "type": ["TRANSFER", "CASH_OUT", "PAYMENT", "TRANSFER"],
            "amount": [1000, 5000, 100, 20000],
            "fraud_score": [0.9, 0.4, 0.2, 0.7],
            "isFraud": [1, 0, 0, 1],
        }
    )


def test_static_threshold_flags_correct_transactions():
    df = sample_transactions()

    result = run_static(df, threshold=0.5)

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
    assert result["rank_score"].tolist() == result["fraud_score"].tolist()


def test_benefit_ranking_creates_expected_benefit():
    df = sample_transactions()

    result = apply_ranking(
        df=df,
        policy="benefit",
        investigation_cost=10,
    )

    assert "expected_benefit" in result.columns
    assert "rank_score" in result.columns

    expected = result["fraud_score"] * result["amount"] - 10

    assert result["expected_benefit"].tolist() == expected.tolist()
    assert result["rank_score"].tolist() == expected.tolist()


def test_risk_zone_policy_keeps_high_risk_and_fills_budget():
    df = sample_transactions()

    result = run_decision_system(
        df=df,
        investigation_cost=10,
        alert_budget=3,
        policy="risk_zone",
        static_threshold=0.5,
        risk_zone_floor=0.3,
    )

    assert "alert" in result.columns
    assert int(result["alert"].sum()) == 3

    selected = result[result["alert"] == 1]

    assert all(selected["fraud_score"] >= 0.3)


def test_invalid_policy_raises_value_error():
    df = sample_transactions()

    with pytest.raises(ValueError):
        apply_ranking(
            df=df,
            policy="invalid_policy",
            investigation_cost=10,
        )


def test_assign_severity_levels():
    assert assign_severity(0.99) == "HIGH"
    assert assign_severity(0.90) == "MEDIUM"
    assert assign_severity(0.50) == "LOW"