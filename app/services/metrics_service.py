def safe_divide(
    numerator: float,
    denominator: float,
) -> float:
    """
    Divide two values safely.

    Returns 0 when the denominator is 0.
    """
    if denominator == 0:
        return 0.0

    return numerator / denominator


def evaluate(
    df,
    alert_col: str,
    investigation_cost: float,
) -> dict:
    """
    Calculate operational fraud detection metrics.
    """
    if alert_col not in df.columns:
        raise ValueError(
            f"Alert column not found: {alert_col}"
        )

    required_columns = {
        "isFraud",
        "amount",
    }

    missing_columns = required_columns.difference(
        df.columns
    )

    if missing_columns:
        raise ValueError(
            "Missing evaluation columns: "
            f"{sorted(missing_columns)}"
        )

    alerts_df = df[
        df[alert_col] == 1
    ].copy()

    missed_frauds_df = df[
        (df["isFraud"] == 1)
        & (df[alert_col] == 0)
    ].copy()

    frauds_total = int(
        df["isFraud"].sum()
    )

    alerts_count = int(
        len(alerts_df)
    )

    frauds_caught = int(
        alerts_df["isFraud"].sum()
    )

    missed_frauds = int(
        len(missed_frauds_df)
    )

    false_positives = int(
        alerts_count - frauds_caught
    )

    precision = safe_divide(
        frauds_caught,
        alerts_count,
    )

    recall = safe_divide(
        frauds_caught,
        frauds_total,
    )

    alert_rate = safe_divide(
        alerts_count,
        len(df),
    )

    missed_fraud_cost = float(
        missed_frauds_df["amount"].sum()
    )

    fraud_loss_prevented = float(
        alerts_df.loc[
            alerts_df["isFraud"] == 1,
            "amount",
        ].sum()
    )

    investigation_cost_total = float(
        alerts_count * investigation_cost
    )

    total_operational_cost = (
        missed_fraud_cost
        + investigation_cost_total
    )

    queue_efficiency = precision

    false_positive_rate_in_queue = safe_divide(
        false_positives,
        alerts_count,
    )

    frauds_per_100_alerts = (
        precision * 100
    )

    cost_per_fraud_caught = safe_divide(
        total_operational_cost,
        frauds_caught,
    )

    missed_fraud_cost_per_transaction = (
        safe_divide(
            missed_fraud_cost,
            len(df),
        )
    )

    operational_cost_per_transaction = (
        safe_divide(
            total_operational_cost,
            len(df),
        )
    )

    return {
        "transactions": int(len(df)),
        "frauds_total": frauds_total,
        "alerts": alerts_count,
        "frauds_caught": frauds_caught,
        "missed_frauds": missed_frauds,
        "false_positives": false_positives,
        "precision": precision,
        "recall": recall,
        "alert_rate": alert_rate,
        "missed_fraud_cost": missed_fraud_cost,
        "fraud_loss_prevented": (
            fraud_loss_prevented
        ),
        "investigation_cost_total": (
            investigation_cost_total
        ),
        "total_operational_cost": (
            total_operational_cost
        ),
        "queue_efficiency": queue_efficiency,
        "false_positive_rate_in_queue": (
            false_positive_rate_in_queue
        ),
        "frauds_per_100_alerts": (
            frauds_per_100_alerts
        ),
        "cost_per_fraud_caught": (
            cost_per_fraud_caught
        ),
        "missed_fraud_cost_per_transaction": (
            missed_fraud_cost_per_transaction
        ),
        "operational_cost_per_transaction": (
            operational_cost_per_transaction
        ),
    }


def build_business_kpis(
    static_metrics: dict,
    decision_metrics: dict,
) -> dict:
    """
    Build business KPIs comparing the static baseline
    with the budget-aware decision system.
    """
    static_cost = static_metrics[
        "total_operational_cost"
    ]

    decision_cost = decision_metrics[
        "total_operational_cost"
    ]

    static_frauds = static_metrics[
        "frauds_caught"
    ]

    decision_frauds = decision_metrics[
        "frauds_caught"
    ]

    static_missed_cost = static_metrics[
        "missed_fraud_cost"
    ]

    decision_missed_cost = decision_metrics[
        "missed_fraud_cost"
    ]

    cost_reduction = (
        static_cost - decision_cost
    )

    missed_fraud_cost_reduction = (
        static_missed_cost
        - decision_missed_cost
    )

    additional_frauds_caught = (
        decision_frauds
        - static_frauds
    )

    return {
        "cost_reduction": cost_reduction,
        "cost_reduction_pct": safe_divide(
            cost_reduction,
            static_cost,
        ),
        "missed_fraud_cost_reduction": (
            missed_fraud_cost_reduction
        ),
        "missed_fraud_cost_reduction_pct": (
            safe_divide(
                missed_fraud_cost_reduction,
                static_missed_cost,
            )
        ),
        "additional_frauds_caught": (
            additional_frauds_caught
        ),
        "fraud_capture_improvement_pct": (
            safe_divide(
                additional_frauds_caught,
                static_frauds,
            )
        ),
        "adaptive_cost_per_fraud_caught": (
            decision_metrics[
                "cost_per_fraud_caught"
            ]
        ),
        "static_cost_per_fraud_caught": (
            static_metrics[
                "cost_per_fraud_caught"
            ]
        ),
        "adaptive_frauds_per_100_alerts": (
            decision_metrics[
                "frauds_per_100_alerts"
            ]
        ),
        "static_frauds_per_100_alerts": (
            static_metrics[
                "frauds_per_100_alerts"
            ]
        ),
        "adaptive_operational_cost_per_transaction": (
            decision_metrics[
                "operational_cost_per_transaction"
            ]
        ),
        "static_operational_cost_per_transaction": (
            static_metrics[
                "operational_cost_per_transaction"
            ]
        ),
    }