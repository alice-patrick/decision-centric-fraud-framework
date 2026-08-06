from collections.abc import Sequence

import pandas as pd

from app.services.decision_service import run_decision_system
from app.services.metrics_service import evaluate


DEFAULT_BUDGET_MULTIPLIERS = (
    1.0,
    1.1,
    1.2,
    1.3,
    1.4,
    1.5,
)


def validate_budget_multipliers(
    budget_multipliers: Sequence[float],
) -> None:
    """
    Validate the budget multipliers used
    to construct the operating curve.
    """
    if len(budget_multipliers) == 0:
        raise ValueError(
            "budget_multipliers must not be empty."
        )

    if any(
        multiplier < 0
        for multiplier in budget_multipliers
    ):
        raise ValueError(
            "All budget multipliers must be non-negative."
        )


def calculate_alert_budget(
    static_alerts: int,
    budget_multiplier: float,
) -> int:
    """
    Calculate the alert budget relative
    to the static baseline alert volume.
    """
    if static_alerts < 0:
        raise ValueError(
            "static_alerts must be non-negative."
        )

    if budget_multiplier < 0:
        raise ValueError(
            "budget_multiplier must be non-negative."
        )

    return int(
        static_alerts * budget_multiplier
    )


def build_operating_curve(
    df: pd.DataFrame,
    static_metrics: dict,
    static_alerts: int,
    investigation_cost: float,
    ranking_policy: str,
    risk_zone_floor: float = 0.3,
    budget_multipliers: Sequence[float] = DEFAULT_BUDGET_MULTIPLIERS,
) -> list[dict]:
    """
    Evaluate the decision system across multiple
    alert-budget multipliers.

    Each operating point is compared with:
    - the static-threshold baseline;
    - the previous operating point.
    """
    validate_budget_multipliers(
        budget_multipliers=budget_multipliers,
    )

    rows: list[dict] = []

    previous_alerts = int(
        static_metrics["alerts"]
    )
    previous_frauds_caught = int(
        static_metrics["frauds_caught"]
    )

    static_operational_cost = float(
        static_metrics["total_operational_cost"]
    )

    for budget_multiplier in budget_multipliers:
        decision_budget = calculate_alert_budget(
            static_alerts=static_alerts,
            budget_multiplier=budget_multiplier,
        )

        decision_df = run_decision_system(
            df=df,
            investigation_cost=investigation_cost,
            alert_budget=decision_budget,
            policy=ranking_policy,
            risk_zone_floor=risk_zone_floor,
        )

        decision_metrics = evaluate(
            df=decision_df,
            alert_col="alert",
            investigation_cost=investigation_cost,
        )

        alerts = int(
            decision_metrics["alerts"]
        )
        frauds_caught = int(
            decision_metrics["frauds_caught"]
        )

        additional_alerts_vs_static = (
            alerts
            - int(static_metrics["alerts"])
        )

        additional_frauds_caught_vs_static = (
            frauds_caught
            - int(static_metrics["frauds_caught"])
        )

        cost_reduction_vs_static = (
            static_operational_cost
            - float(
                decision_metrics[
                    "total_operational_cost"
                ]
            )
        )

        if static_operational_cost != 0:
            cost_reduction_pct_vs_static = (
                cost_reduction_vs_static
                / static_operational_cost
            )
        else:
            cost_reduction_pct_vs_static = 0.0

        marginal_alerts = (
            alerts
            - previous_alerts
        )

        marginal_frauds_caught = (
            frauds_caught
            - previous_frauds_caught
        )

        if marginal_alerts > 0:
            marginal_frauds_per_100_alerts = (
                marginal_frauds_caught
                / marginal_alerts
            ) * 100
        else:
            marginal_frauds_per_100_alerts = 0.0

        row = {
            "budget_multiplier": float(
                budget_multiplier
            ),
            "alert_budget": int(
                decision_budget
            ),
            "alerts": alerts,
            "frauds_caught": frauds_caught,
            "missed_frauds": int(
                decision_metrics[
                    "missed_frauds"
                ]
            ),
            "false_positives": int(
                decision_metrics[
                    "false_positives"
                ]
            ),
            "recall": float(
                decision_metrics["recall"]
            ),
            "precision": float(
                decision_metrics["precision"]
            ),
            "alert_rate": float(
                decision_metrics["alert_rate"]
            ),
            "missed_fraud_cost": float(
                decision_metrics[
                    "missed_fraud_cost"
                ]
            ),
            "fraud_loss_prevented": float(
                decision_metrics[
                    "fraud_loss_prevented"
                ]
            ),
            "investigation_cost_total": float(
                decision_metrics[
                    "investigation_cost_total"
                ]
            ),
            "total_operational_cost": float(
                decision_metrics[
                    "total_operational_cost"
                ]
            ),
            "queue_efficiency": float(
                decision_metrics[
                    "queue_efficiency"
                ]
            ),
            "false_positive_rate_in_queue": float(
                decision_metrics[
                    "false_positive_rate_in_queue"
                ]
            ),
            "frauds_per_100_alerts": float(
                decision_metrics[
                    "frauds_per_100_alerts"
                ]
            ),
            "cost_per_fraud_caught": float(
                decision_metrics[
                    "cost_per_fraud_caught"
                ]
            ),
            "operational_cost_per_transaction": float(
                decision_metrics[
                    "operational_cost_per_transaction"
                ]
            ),
            "additional_alerts_vs_static": int(
                additional_alerts_vs_static
            ),
            "additional_frauds_caught_vs_static": int(
                additional_frauds_caught_vs_static
            ),
            "cost_reduction_vs_static": float(
                cost_reduction_vs_static
            ),
            "cost_reduction_pct_vs_static": float(
                cost_reduction_pct_vs_static
            ),
            "marginal_alerts": int(
                marginal_alerts
            ),
            "marginal_frauds_caught": int(
                marginal_frauds_caught
            ),
            "marginal_frauds_per_100_alerts": float(
                marginal_frauds_per_100_alerts
            ),
            "cost_diff_vs_static": float(
                decision_metrics[
                    "total_operational_cost"
                ]
                - static_operational_cost
            ),
            "recall_diff_vs_static": float(
                decision_metrics["recall"]
                - static_metrics["recall"]
            ),
            "precision_diff_vs_static": float(
                decision_metrics["precision"]
                - static_metrics["precision"]
            ),
        }

        rows.append(row)

        previous_alerts = alerts
        previous_frauds_caught = frauds_caught

    return rows