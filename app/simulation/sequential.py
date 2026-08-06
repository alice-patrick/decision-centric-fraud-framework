from __future__ import annotations

from typing import Any

import pandas as pd


REQUIRED_SIMULATION_COLUMNS = [
    "step",
    "transaction_id",
    "simulation_entity_key",
    "amount",
    "fraud_score",
    "rank_score",
    "isFraud",
    "policy_alert_candidate",
]


def validate_sequential_input(
    alerts_df: pd.DataFrame,
) -> None:
    """
    Validate the DataFrame provided to the sequential simulation.

    The simulation does not create alerts itself. It expects the
    selected decision policy to have already created the Boolean
    column `policy_alert_candidate`.
    """
    if alerts_df.empty:
        raise ValueError(
            "The sequential simulation input is empty."
        )

    missing_columns = [
        column
        for column in REQUIRED_SIMULATION_COLUMNS
        if column not in alerts_df.columns
    ]

    if missing_columns:
        raise ValueError(
            "Sequential simulation input is missing "
            f"required columns: {missing_columns}"
        )

    if alerts_df["step"].isna().any():
        raise ValueError(
            "The 'step' column contains missing values."
        )

    if alerts_df["transaction_id"].isna().any():
        raise ValueError(
            "The 'transaction_id' column contains "
            "missing values."
        )

    if alerts_df["rank_score"].isna().any():
        raise ValueError(
            "The 'rank_score' column contains missing values."
        )

    if alerts_df["isFraud"].isna().any():
        raise ValueError(
            "The 'isFraud' column contains missing values."
        )


def run_sequential_simulation(
    alerts_df: pd.DataFrame,
    alert_budget_per_step: int,
    suppression_window: int,
) -> pd.DataFrame:
    """
    Apply chronological capacity and suppression rules to policy alerts.

    The decision policy has already generated:
    - `policy_alert_candidate`
    - `rank_score`
    - `fraud_score`

    Within every chronological step, candidate alerts are explicitly
    prioritised by descending rank score and fraud score. Suppression is
    evaluated first; the remaining highest-priority alerts are accepted
    until the per-step analyst capacity is exhausted.

    The function also creates audit columns that can be used directly by
    the Analyst Queue UI.
    """
    if alert_budget_per_step < 1:
        raise ValueError(
            "alert_budget_per_step must be at least 1."
        )

    if suppression_window < 0:
        raise ValueError(
            "suppression_window cannot be negative."
        )

    validate_sequential_input(alerts_df)

    simulated_df = alerts_df.copy()

    simulated_df["policy_alert_candidate"] = (
        simulated_df["policy_alert_candidate"]
        .fillna(False)
        .astype(bool)
    )

    simulated_df["isFraud"] = (
        simulated_df["isFraud"]
        .fillna(0)
        .astype(int)
    )

    simulated_df["rank_score"] = pd.to_numeric(
        simulated_df["rank_score"],
        errors="coerce",
    )

    simulated_df["fraud_score"] = pd.to_numeric(
        simulated_df["fraud_score"],
        errors="coerce",
    )

    if simulated_df["rank_score"].isna().any():
        raise ValueError(
            "The 'rank_score' column contains non-numeric values."
        )

    if simulated_df["fraud_score"].isna().any():
        raise ValueError(
            "The 'fraud_score' column contains non-numeric values."
        )

    # Keep the original row identity so that the final output can be
    # restored to chronological transaction order.
    simulated_df["_original_row_order"] = range(len(simulated_df))

    # Output and audit columns.
    simulated_df["selected_alert"] = False
    simulated_df["suppression_applied"] = False
    simulated_df["capacity_rejected"] = False
    simulated_df["sequential_decision"] = "no_alert"
    simulated_df["candidate_priority_rank"] = pd.NA
    simulated_df["accepted_priority_rank"] = pd.NA
    simulated_df["capacity_used_before_decision"] = 0
    simulated_df["capacity_remaining_after_decision"] = (
        alert_budget_per_step
    )

    # Most recent chronological step at which an entity generated an
    # accepted alert.
    last_accepted_alert_step: dict[str, int] = {}

    unique_steps = sorted(
        simulated_df["step"]
        .dropna()
        .unique()
        .tolist()
    )

    for current_step in unique_steps:
        step_candidate_mask = (
            (simulated_df["step"] == current_step)
            & simulated_df["policy_alert_candidate"]
        )

        # Ranking is performed explicitly inside each chronological
        # step. This prevents the sequential engine from selecting rows
        # according to their original DataFrame order.
        step_candidates = (
            simulated_df.loc[step_candidate_mask]
            .sort_values(
                by=[
                    "rank_score",
                    "fraud_score",
                    "transaction_id",
                ],
                ascending=[
                    False,
                    False,
                    True,
                ],
                kind="mergesort",
            )
        )

        for priority_rank, row_index in enumerate(
            step_candidates.index,
            start=1,
        ):
            simulated_df.at[
                row_index,
                "candidate_priority_rank",
            ] = priority_rank

        accepted_alerts_in_step = 0

        for row_index in step_candidates.index:
            entity_key = str(
                simulated_df.at[
                    row_index,
                    "simulation_entity_key",
                ]
            )

            current_step_value = int(current_step)
            previous_alert_step = (
                last_accepted_alert_step.get(entity_key)
            )

            repeated_within_window = False

            if (
                suppression_window > 0
                and previous_alert_step is not None
            ):
                step_difference = (
                    current_step_value
                    - previous_alert_step
                )
                repeated_within_window = (
                    step_difference <= suppression_window
                )

            simulated_df.at[
                row_index,
                "capacity_used_before_decision",
            ] = accepted_alerts_in_step

            if repeated_within_window:
                simulated_df.at[
                    row_index,
                    "suppression_applied",
                ] = True
                simulated_df.at[
                    row_index,
                    "sequential_decision",
                ] = "suppressed"
                simulated_df.at[
                    row_index,
                    "capacity_remaining_after_decision",
                ] = (
                    alert_budget_per_step
                    - accepted_alerts_in_step
                )
                continue

            if (
                accepted_alerts_in_step
                >= alert_budget_per_step
            ):
                simulated_df.at[
                    row_index,
                    "capacity_rejected",
                ] = True
                simulated_df.at[
                    row_index,
                    "sequential_decision",
                ] = "capacity_rejected"
                simulated_df.at[
                    row_index,
                    "capacity_remaining_after_decision",
                ] = 0
                continue

            accepted_alerts_in_step += 1

            simulated_df.at[
                row_index,
                "selected_alert",
            ] = True
            simulated_df.at[
                row_index,
                "sequential_decision",
            ] = "alert"
            simulated_df.at[
                row_index,
                "accepted_priority_rank",
            ] = accepted_alerts_in_step
            simulated_df.at[
                row_index,
                "capacity_remaining_after_decision",
            ] = (
                alert_budget_per_step
                - accepted_alerts_in_step
            )

            last_accepted_alert_step[
                entity_key
            ] = current_step_value

        print(
            f"Step {current_step}: "
            f"accepted={accepted_alerts_in_step}, "
            f"remaining_capacity={alert_budget_per_step - accepted_alerts_in_step}"
        )

    # Use nullable integer columns for clean API and dashboard output.
    simulated_df["candidate_priority_rank"] = (
        simulated_df["candidate_priority_rank"]
        .astype("Int64")
    )
    simulated_df["accepted_priority_rank"] = (
        simulated_df["accepted_priority_rank"]
        .astype("Int64")
    )

    # Restore chronological transaction order for monitoring and UI use.
    simulated_df = (
        simulated_df.sort_values(
            by=[
                "step",
                "transaction_id",
                "_original_row_order",
            ],
            ascending=[
                True,
                True,
                True,
            ],
            kind="mergesort",
        )
        .drop(columns=["_original_row_order"])
        .reset_index(drop=True)
    )

    return simulated_df


def build_operational_step_breakdown(
    df: pd.DataFrame,
    alert_budget_per_step: int,
) -> pd.DataFrame:
    """
    Aggregate the sequential audit columns by operational step.

    The resulting table explains how candidate alerts move through
    suppression and analyst capacity during each chronological decision
    cycle. It is intended for the Analyst Capacity dashboard section,
    not for monitoring-window trend analysis.
    """
    if df.empty:
        raise ValueError(
            "Cannot build an operational-step breakdown from an empty DataFrame."
        )

    if alert_budget_per_step < 1:
        raise ValueError(
            "alert_budget_per_step must be at least 1."
        )

    required_columns = [
        "step",
        "policy_alert_candidate",
        "suppression_applied",
        "selected_alert",
        "capacity_rejected",
    ]

    missing_columns = [
        column
        for column in required_columns
        if column not in df.columns
    ]

    if missing_columns:
        raise ValueError(
            "Operational-step breakdown is missing required columns: "
            f"{missing_columns}"
        )

    records: list[dict[str, Any]] = []

    for step_value, step_df in df.groupby("step", sort=True):
        candidate_alerts = int(
            step_df["policy_alert_candidate"]
            .fillna(False)
            .astype(bool)
            .sum()
        )
        suppressed_alerts = int(
            step_df["suppression_applied"]
            .fillna(False)
            .astype(bool)
            .sum()
        )
        investigated_alerts = int(
            step_df["selected_alert"]
            .fillna(False)
            .astype(bool)
            .sum()
        )
        capacity_rejected_alerts = int(
            step_df["capacity_rejected"]
            .fillna(False)
            .astype(bool)
            .sum()
        )

        eligible_alerts = max(
            candidate_alerts - suppressed_alerts,
            0,
        )
        unused_capacity = max(
            alert_budget_per_step - investigated_alerts,
            0,
        )

        if capacity_rejected_alerts > 0:
            capacity_status = "Over capacity"
        elif unused_capacity > 0:
            capacity_status = "Capacity available"
        else:
            capacity_status = "Fully utilised"

        records.append(
            {
                "step": int(step_value),
                "candidate_alerts": candidate_alerts,
                "suppressed_alerts": suppressed_alerts,
                "eligible_alerts": eligible_alerts,
                "investigated_alerts": investigated_alerts,
                "capacity_rejected_alerts": capacity_rejected_alerts,
                "analyst_capacity": int(alert_budget_per_step),
                "unused_capacity": unused_capacity,
                "capacity_status": capacity_status,
            }
        )

    return pd.DataFrame(records)


def evaluate_sequential_results(
    df: pd.DataFrame,
    investigation_cost_per_alert: float,
    false_negative_factor: float = 1.0,
) -> dict[str, Any]:
    """
    Calculate fraud-detection and operational metrics.

    A fraud is considered detected only when its transaction becomes
    an accepted sequential alert.
    """
    if df.empty:
        raise ValueError(
            "Cannot evaluate an empty simulation result."
        )

    required_columns = [
        "amount",
        "isFraud",
        "policy_alert_candidate",
        "selected_alert",
        "suppression_applied",
        "capacity_rejected",
    ]

    missing_columns = [
        column
        for column in required_columns
        if column not in df.columns
    ]

    if missing_columns:
        raise ValueError(
            "Sequential results are missing required "
            f"columns: {missing_columns}"
        )

    if investigation_cost_per_alert < 0:
        raise ValueError(
            "investigation_cost_per_alert cannot be negative."
        )

    if false_negative_factor < 0:
        raise ValueError(
            "false_negative_factor cannot be negative."
        )

    total_transactions = int(len(df))

    total_frauds = int(
        df["isFraud"].sum()
    )

    policy_candidate_alerts = int(
        df["policy_alert_candidate"].sum()
    )

    selected_alerts = int(
        df["selected_alert"].sum()
    )

    suppressed_alerts = int(
        df["suppression_applied"].sum()
    )

    capacity_rejected_alerts = int(
        df["capacity_rejected"].sum()
    )

    detected_fraud_mask = (
        df["selected_alert"]
        & (df["isFraud"] == 1)
    )

    missed_fraud_mask = (
        (~df["selected_alert"])
        & (df["isFraud"] == 1)
    )

    false_positive_mask = (
        df["selected_alert"]
        & (df["isFraud"] == 0)
    )

    suppressed_fraud_mask = (
        df["suppression_applied"]
        & (df["isFraud"] == 1)
    )

    capacity_rejected_fraud_mask = (
        df["capacity_rejected"]
        & (df["isFraud"] == 1)
    )

    frauds_detected = int(
        detected_fraud_mask.sum()
    )

    frauds_missed = int(
        missed_fraud_mask.sum()
    )

    false_positives = int(
        false_positive_mask.sum()
    )

    suppressed_frauds = int(
        suppressed_fraud_mask.sum()
    )

    capacity_rejected_frauds = int(
        capacity_rejected_fraud_mask.sum()
    )

    precision = (
        frauds_detected / selected_alerts
        if selected_alerts > 0
        else 0.0
    )

    recall = (
        frauds_detected / total_frauds
        if total_frauds > 0
        else 0.0
    )

    suppression_rate = (
        suppressed_alerts / policy_candidate_alerts
        if policy_candidate_alerts > 0
        else 0.0
    )

    alert_acceptance_rate = (
        selected_alerts / policy_candidate_alerts
        if policy_candidate_alerts > 0
        else 0.0
    )

    investigation_cost_total = (
        selected_alerts
        * investigation_cost_per_alert
    )

    missed_fraud_cost = float(
        (
            df.loc[
                missed_fraud_mask,
                "amount",
            ]
            * false_negative_factor
        ).sum()
    )

    fraud_loss_prevented = float(
        (
            df.loc[
                detected_fraud_mask,
                "amount",
            ]
            * false_negative_factor
        ).sum()
    )

    total_operational_cost = (
        investigation_cost_total
        + missed_fraud_cost
    )

    return {
        "total_transactions": total_transactions,
        "total_frauds": total_frauds,
        "policy_candidate_alerts": (
            policy_candidate_alerts
        ),
        "selected_alerts": selected_alerts,
        "suppressed_alerts": suppressed_alerts,
        "capacity_rejected_alerts": (
            capacity_rejected_alerts
        ),
        "frauds_detected": frauds_detected,
        "frauds_missed": frauds_missed,
        "false_positives": false_positives,
        "suppressed_frauds": suppressed_frauds,
        "capacity_rejected_frauds": (
            capacity_rejected_frauds
        ),
        "precision": round(
            precision,
            6,
        ),
        "recall": round(
            recall,
            6,
        ),
        "suppression_rate": round(
            suppression_rate,
            6,
        ),
        "alert_acceptance_rate": round(
            alert_acceptance_rate,
            6,
        ),
        "investigation_cost_total": round(
            investigation_cost_total,
            2,
        ),
        "missed_fraud_cost": round(
            missed_fraud_cost,
            2,
        ),
        "fraud_loss_prevented": round(
            fraud_loss_prevented,
            2,
        ),
        "total_operational_cost": round(
            total_operational_cost,
            2,
        ),
    }


def build_monitoring_windows(
    df: pd.DataFrame,
    investigation_cost_per_alert: float,
    window_size: int = 1000,
    false_negative_factor: float = 1.0,
) -> pd.DataFrame:
    """
    Divide chronological results into monitoring windows.

    Each monitoring window contains the same evaluation metrics as
    the complete sequential simulation.
    """
    if df.empty:
        raise ValueError(
            "Cannot build monitoring windows from an "
            "empty DataFrame."
        )

    if window_size < 1:
        raise ValueError(
            "window_size must be at least 1."
        )

    monitoring_df = (
        df.sort_values(
            by=[
                "step",
                "transaction_id",
            ],
            ascending=[
                True,
                True,
            ],
        )
        .reset_index(drop=True)
        .copy()
    )

    monitoring_df["monitoring_window"] = (
        monitoring_df.index // window_size
    ) + 1

    records: list[dict[str, Any]] = []

    for window_number, window_df in (
        monitoring_df.groupby(
            "monitoring_window",
            sort=True,
        )
    ):
        window_summary = evaluate_sequential_results(
            df=window_df,
            investigation_cost_per_alert=(
                investigation_cost_per_alert
            ),
            false_negative_factor=(
                false_negative_factor
            ),
        )

        record = {
            "monitoring_window": int(
                window_number
            ),
            "start_row": int(
                window_df.index.min()
            ),
            "end_row": int(
                window_df.index.max()
            ),
            "start_step": int(
                window_df["step"].min()
            ),
            "end_step": int(
                window_df["step"].max()
            ),
            **window_summary,
        }

        records.append(record)

    return pd.DataFrame(records)