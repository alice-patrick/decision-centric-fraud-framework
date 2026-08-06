import requests

API_BASE_URL = "http://127.0.0.1:8000"


def test_comparison_endpoint():
    response = requests.get(
        f"{API_BASE_URL}/comparison",
        params={
            "limit": 1000,
            "investigation_cost": 10,
            "ranking_policy": "risk_zone",
            "risk_zone_floor": 0.3,
            "budget_multiplier": 1.2,
        },
        timeout=120,
    )

    assert response.status_code == 200

    data = response.json()

    assert "static" in data
    assert "decision_system" in data
    assert "cost_diff" in data
    assert "recall_diff" in data
    assert "precision_diff" in data

    assert data["static"]["alerts"] >= 0
    assert data["decision_system"]["alerts"] >= 0


def test_alerts_endpoint():
    response = requests.get(
        f"{API_BASE_URL}/alerts",
        params={
            "limit": 1000,
            "investigation_cost": 10,
            "ranking_policy": "risk_zone",
            "risk_zone_floor": 0.3,
            "budget_multiplier": 1.2,
        },
        timeout=120,
    )

    assert response.status_code == 200

    data = response.json()

    assert isinstance(data, list)

    if len(data) > 0:
        first_alert = data[0]

        assert "transaction_id" in first_alert
        assert "amount" in first_alert
        assert "fraud_score" in first_alert
        assert "rank_score" in first_alert
        assert "expected_benefit" in first_alert
        assert "severity" in first_alert
        assert "reason" in first_alert
        assert "isFraud" in first_alert

        assert first_alert["severity"] in ["HIGH", "MEDIUM", "LOW"]


def test_operating_curve_endpoint():
    response = requests.get(
        f"{API_BASE_URL}/operating_curve",
        params={
            "limit": 1000,
            "investigation_cost": 10,
            "ranking_policy": "risk_zone",
            "risk_zone_floor": 0.3,
        },
        timeout=120,
    )

    assert response.status_code == 200

    data = response.json()

    assert "static_baseline" in data
    assert "operating_curve" in data

    curve = data["operating_curve"]

    assert isinstance(curve, list)
    assert len(curve) > 0

    first_row = curve[0]

    assert "budget_multiplier" in first_row
    assert "alerts" in first_row
    assert "frauds_caught" in first_row
    assert "recall" in first_row
    assert "precision" in first_row
    assert "total_cost" in first_row
    assert "cost_diff_vs_static" in first_row


def test_invalid_ranking_policy_returns_error():
    response = requests.get(
        f"{API_BASE_URL}/comparison",
        params={
            "limit": 1000,
            "investigation_cost": 10,
            "ranking_policy": "invalid_policy",
            "risk_zone_floor": 0.3,
            "budget_multiplier": 1.2,
        },
        timeout=120,
    )

    assert response.status_code >= 400