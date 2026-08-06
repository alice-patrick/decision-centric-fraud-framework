import requests

API_BASE_URL = "http://127.0.0.1:8000"


def test_operating_curve_returns_expected_structure():
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

    assert "parameters" in data
    assert "static_baseline" in data
    assert "operating_curve" in data

    curve = data["operating_curve"]

    assert isinstance(curve, list)
    assert len(curve) == 6


def test_budget_multiplier_is_increasing():
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

    curve = response.json()["operating_curve"]

    multipliers = [row["budget_multiplier"] for row in curve]

    assert multipliers == sorted(multipliers)


def test_alert_budget_does_not_decrease():
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

    curve = response.json()["operating_curve"]

    alert_budgets = [row["alert_budget"] for row in curve]

    assert alert_budgets == sorted(alert_budgets)


def test_alerts_do_not_decrease_when_budget_increases():
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

    curve = response.json()["operating_curve"]

    alerts = [row["alerts"] for row in curve]

    assert alerts == sorted(alerts)


def test_recall_is_valid_probability():
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

    curve = response.json()["operating_curve"]

    for row in curve:
        assert 0 <= row["recall"] <= 1


def test_precision_is_valid_probability():
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

    curve = response.json()["operating_curve"]

    for row in curve:
        assert 0 <= row["precision"] <= 1