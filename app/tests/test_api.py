from fastapi.testclient import TestClient

from app.api.main import app


client = TestClient(
    app,
    raise_server_exceptions=False,
)


def test_root_redirects_to_docs():
    response = client.get(
        "/",
        follow_redirects=False,
    )

    assert response.status_code in {
        302,
        307,
    }

    assert response.headers[
        "location"
    ] == "/docs"


def test_comparison_endpoint_returns_expected_structure():
    response = client.get(
        "/comparison",
        params={
            "limit": 1000,
            "investigation_cost": 10,
            "ranking_policy": "risk_zone",
            "risk_zone_floor": 0.3,
            "budget_multiplier": 1.2,
        },
    )

    assert response.status_code == 200

    data = response.json()

    expected_top_level_fields = {
        "parameters",
        "static",
        "decision_system",
        "business_kpis",
        "cost_diff",
        "recall_diff",
        "precision_diff",
        "missed_fraud_cost_diff",
        "fraud_loss_prevented_diff",
    }

    assert expected_top_level_fields.issubset(
        data.keys()
    )

    assert data["static"]["alerts"] >= 0

    assert (
        data["decision_system"]["alerts"]
        >= 0
    )


def test_comparison_parameters_match_request():
    response = client.get(
        "/comparison",
        params={
            "limit": 1000,
            "investigation_cost": 10,
            "ranking_policy": "risk_zone",
            "risk_zone_floor": 0.3,
            "budget_multiplier": 1.2,
        },
    )

    assert response.status_code == 200

    parameters = response.json()[
        "parameters"
    ]

    assert parameters["limit"] == 1000

    assert parameters[
        "investigation_cost"
    ] == 10

    assert parameters[
        "ranking_policy"
    ] == "risk_zone"

    assert parameters[
        "risk_zone_floor"
    ] == 0.3

    assert parameters[
        "budget_multiplier"
    ] == 1.2


def test_alerts_endpoint_returns_prioritised_queue():
    analyst_capacity = 25

    response = client.get(
        "/alerts",
        params={
            "limit": 1000,
            "investigation_cost": 10,
            "ranking_policy": "risk_zone",
            "risk_zone_floor": 0.3,
            "budget_multiplier": 1.2,
            "analyst_capacity": (
                analyst_capacity
            ),
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert isinstance(data, list)

    assert len(data) <= analyst_capacity

    if len(data) > 0:
        first_alert = data[0]

        expected_fields = {
            "transaction_id",
            "step",
            "type",
            "amount",
            "fraud_score",
            "rank_score",
            "expected_benefit",
            "expected_investigation_cost",
            "alert",
            "selected_for_review",
            "queue_position",
            "severity",
            "analyst_priority",
            "reason",
            "isFraud",
        }

        assert expected_fields.issubset(
            first_alert.keys()
        )

        assert (
            first_alert[
                "selected_for_review"
            ]
            == 1
        )

        assert first_alert[
            "severity"
        ] in {
            "CRITICAL",
            "HIGH",
            "MEDIUM",
            "LOW",
        }


def test_alert_queue_positions_are_ordered():
    response = client.get(
        "/alerts",
        params={
            "limit": 1000,
            "analyst_capacity": 25,
        },
    )

    assert response.status_code == 200

    data = response.json()

    queue_positions = [
        row["queue_position"]
        for row in data
    ]

    assert queue_positions == sorted(
        queue_positions
    )


def test_decision_export_returns_expected_fields():
    response = client.get(
        "/decision_export",
        params={
            "limit": 1000,
            "investigation_cost": 10,
            "ranking_policy": "risk_zone",
            "risk_zone_floor": 0.3,
            "budget_multiplier": 1.2,
            "analyst_capacity": 25,
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert isinstance(data, list)

    if len(data) > 0:
        first_row = data[0]

        expected_fields = {
            "transaction_id",
            "fraud_score",
            "rank_score",
            "static_alert",
            "adaptive_alert",
            "adaptive_gain_fraud",
            "selected_for_review",
            "queue_position",
            "budget_overflow",
            "severity",
            "reason",
            "isFraud",
        }

        assert expected_fields.issubset(
            first_row.keys()
        )


def test_operating_curve_endpoint_returns_expected_structure():
    response = client.get(
        "/operating_curve",
        params={
            "limit": 1000,
            "investigation_cost": 10,
            "ranking_policy": "risk_zone",
            "risk_zone_floor": 0.3,
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert "parameters" in data
    assert "static_baseline" in data
    assert "operating_curve" in data

    curve = data["operating_curve"]

    assert isinstance(curve, list)

    assert len(curve) == 6


def test_operating_curve_rows_have_expected_fields():
    response = client.get(
        "/operating_curve",
        params={
            "limit": 1000,
            "investigation_cost": 10,
            "ranking_policy": "risk_zone",
            "risk_zone_floor": 0.3,
        },
    )

    assert response.status_code == 200

    curve = response.json()[
        "operating_curve"
    ]

    first_row = curve[0]

    expected_fields = {
        "budget_multiplier",
        "alert_budget",
        "alerts",
        "frauds_caught",
        "missed_frauds",
        "recall",
        "precision",
        "total_operational_cost",
        "cost_diff_vs_static",
        "recall_diff_vs_static",
        "precision_diff_vs_static",
    }

    assert expected_fields.issubset(
        first_row.keys()
    )


def test_operating_curve_probabilities_are_valid():
    response = client.get(
        "/operating_curve",
        params={
            "limit": 1000,
            "investigation_cost": 10,
            "ranking_policy": "risk_zone",
            "risk_zone_floor": 0.3,
        },
    )

    assert response.status_code == 200

    curve = response.json()[
        "operating_curve"
    ]

    for row in curve:
        assert (
            0 <= row["recall"] <= 1
        )

        assert (
            0 <= row["precision"] <= 1
        )


def test_sequential_endpoint_returns_four_scenarios():
    response = client.get(
        "/simulation/sequential",
        params={
            "limit": 1000,
            "investigation_cost": 10,
            "static_threshold": 0.5,
            "budget_multiplier": 1.2,
            "ranking_policy": "risk_zone",
            "risk_zone_floor": 0.3,
            "alert_budget_per_step": 10,
            "suppression_window": 3,
            "monitoring_window_size": 250,
        },
    )

    assert response.status_code == 200

    data = response.json()

    expected_fields = {
        "parameters",
        "static_batch",
        "static_sequential",
        "adaptive_batch",
        "adaptive_sequential",
        "scenario_comparison",
        "comparison_differences",
    }

    assert expected_fields.issubset(
        data.keys()
    )

    assert len(
        data["scenario_comparison"]
    ) == 4


def test_sequential_accounting_is_consistent():
    response = client.get(
        "/simulation/sequential",
        params={
            "limit": 1000,
            "alert_budget_per_step": 10,
            "suppression_window": 3,
        },
    )

    assert response.status_code == 200

    data = response.json()

    for key in [
        "static_sequential",
        "adaptive_sequential",
    ]:
        summary = data[key][
            "summary"
        ]

        candidates = summary[
            "policy_candidate_alerts"
        ]

        accounted = (
            summary[
                "selected_alerts"
            ]
            + summary[
                "suppressed_alerts"
            ]
            + summary[
                "capacity_rejected_alerts"
            ]
        )

        assert candidates == accounted


def test_invalid_sequential_capacity_returns_validation_error():
    response = client.get(
        "/simulation/sequential",
        params={
            "limit": 1000,
            "alert_budget_per_step": 0,
        },
    )

    assert response.status_code == 422


def test_invalid_sequential_suppression_window_returns_validation_error():
    response = client.get(
        "/simulation/sequential",
        params={
            "limit": 1000,
            "suppression_window": -1,
        },
    )

    assert response.status_code == 422


def test_invalid_ranking_policy_returns_error():
    response = client.get(
        "/comparison",
        params={
            "limit": 1000,
            "investigation_cost": 10,
            "ranking_policy": (
                "invalid_policy"
            ),
            "risk_zone_floor": 0.3,
            "budget_multiplier": 1.2,
        },
    )

    assert response.status_code >= 400