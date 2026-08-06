from __future__ import annotations

from pathlib import Path
from typing import Any

import pandas as pd
from fastapi import APIRouter, HTTPException, Query

from app.services.data_service import load_data
from app.services.model_service import (
    load_active_model,
    score_data,
)
from app.simulation.sequential import (
    build_monitoring_windows,
    build_operational_step_breakdown,
    evaluate_sequential_results,
    run_sequential_simulation,
)
from app.services.decision_service import (
    run_decision_system,
    run_static,
)
from app.services.operating_curve_service import (
    calculate_alert_budget,
)


PROJECT_ROOT = Path(__file__).resolve().parents[2]


router = APIRouter(
    prefix="/simulation",
    tags=["Simulation"],
)


# =========================================================
# BASE DATA
# =========================================================
def prepare_base_data(
    limit: int,
) -> pd.DataFrame:
    """
    Load transaction data, apply the active fraud model and prepare
    the common dataset used by all four evaluation scenarios:

    1. Static Batch
    2. Static Sequential
    3. Adaptive Batch
    4. Adaptive Sequential
    """
    _, model = load_active_model()

    df = load_data(
        project_root=PROJECT_ROOT,
        limit=limit,
    )

    df = score_data(
        df=df,
        model=model,
    )

    df = df.copy()

    required_columns = [
        "step",
        "type",
        "amount",
        "fraud_score",
        "isFraud",
    ]

    missing_columns = [
        column
        for column in required_columns
        if column not in df.columns
    ]

    if missing_columns:
        raise ValueError(
            f"Missing required columns: {missing_columns}"
        )

    if df.empty:
        raise ValueError(
            "The simulation dataset is empty."
        )

    if df["step"].isna().any():
        raise ValueError(
            "The 'step' column contains missing values."
        )

    if df["amount"].isna().any():
        raise ValueError(
            "The 'amount' column contains missing values."
        )

    if df["fraud_score"].isna().any():
        raise ValueError(
            "The 'fraud_score' column contains missing values."
        )

    df["isFraud"] = (
        df["isFraud"]
        .fillna(0)
        .astype(int)
    )

    df = (
        df.sort_values(
            by=[
                "step",
            ],
            ascending=[
                True,
            ],
        )
        .reset_index(drop=True)
    )

    if "transaction_id" not in df.columns:
        df["transaction_id"] = (
            df.index.astype(str)
        )
    else:
        df["transaction_id"] = (
            df["transaction_id"].astype(str)
        )

    # Proxy key used only for the suppression simulation.
    # It is not a real customer or account identifier.
    df["simulation_entity_key"] = (
        df["type"].astype(str)
        + "_"
        + df["amount"]
        .round(-2)
        .astype(int)
        .astype(str)
    )

    return df


# =========================================================
# COMMON STRATEGY FORMAT
# =========================================================
def convert_strategy_output_to_batch(
    strategy_df: pd.DataFrame,
) -> pd.DataFrame:
    """
    Convert the strategy output to the common batch format.

    The strategy classes produce a `decision` column, while the
    evaluation and sequential layers expect an `alert` column.
    """
    if "decision" not in strategy_df.columns:
        raise ValueError(
            "Strategy output does not contain the "
            "'decision' column."
        )

    batch_df = strategy_df.copy()

    batch_df["alert"] = (
        batch_df["decision"]
        .fillna(0)
        .astype(int)
    )

    return batch_df


# =========================================================
# STATIC BATCH
# =========================================================
def run_static_batch(
    base_df: pd.DataFrame,
    static_threshold: float,
    investigation_cost: float,
) -> pd.DataFrame:
    """
    Run the same static-threshold baseline used by the main API.

    Reusing `run_static` guarantees that the batch results in the
    simulation dashboard remain identical to the validated results
    returned by the `/comparison` endpoint.
    """
    static_df = run_static(
        df=base_df,
        threshold=static_threshold,
        investigation_cost=investigation_cost,
    ).copy()

    if "alert" not in static_df.columns:
        raise ValueError(
            "run_static did not return the required 'alert' column."
        )

    static_df["decision"] = (
        static_df["alert"]
        .fillna(0)
        .astype(int)
    )

    static_df["policy_name"] = "static"
    static_df["strategy"] = "static_threshold"
    static_df["threshold_used"] = static_threshold

    if "rank_score" not in static_df.columns:
        static_df["rank_score"] = static_df["fraud_score"]

    if "expected_fraud_loss" not in static_df.columns:
        static_df["expected_fraud_loss"] = 0.0

    if "expected_investigation_cost" not in static_df.columns:
        static_df["expected_investigation_cost"] = 0.0

    if "expected_benefit" not in static_df.columns:
        static_df["expected_benefit"] = (
            static_df["expected_fraud_loss"]
            - static_df["expected_investigation_cost"]
        )

    return static_df


# =========================================================
# ADAPTIVE BATCH
# =========================================================
def calculate_current_alert_rate(
    df: pd.DataFrame,
    threshold: float,
) -> float:
    """
    Calculate the static-threshold alert rate for reporting purposes.
    """
    if df.empty:
        return 0.0

    alert_count = int(
        (
            df["fraud_score"]
            >= threshold
        ).sum()
    )

    return float(
        alert_count / len(df)
    )


def run_adaptive_batch(
    base_df: pd.DataFrame,
    base_threshold: float,
    adaptive_alert_budget: int,
    investigation_cost: float,
    ranking_policy: str,
    risk_zone_floor: float,
) -> tuple[pd.DataFrame, float]:
    """
    Run the same adaptive decision system used by the main API.

    The simulation layer must evaluate the existing Decision Layer;
    it must not create a second adaptive-policy implementation.
    Therefore this function delegates alert generation and ranking to
    `run_decision_system`, exactly like `/comparison`, `/alerts` and
    `/decision_export`.

    Returns
    -------
    tuple
        adaptive_df,
        current_static_alert_rate
    """
    if adaptive_alert_budget < 0:
        raise ValueError(
            "adaptive_alert_budget cannot be negative."
        )

    if investigation_cost < 0:
        raise ValueError(
            "investigation_cost cannot be negative."
        )

    current_alert_rate = calculate_current_alert_rate(
        df=base_df,
        threshold=base_threshold,
    )

    adaptive_df = run_decision_system(
        df=base_df,
        investigation_cost=investigation_cost,
        alert_budget=adaptive_alert_budget,
        policy=ranking_policy,
        risk_zone_floor=risk_zone_floor,
    ).copy()

    if "alert" not in adaptive_df.columns:
        raise ValueError(
            "run_decision_system did not return the required "
            "'alert' column."
        )

    adaptive_df["decision"] = (
        adaptive_df["alert"]
        .fillna(0)
        .astype(int)
    )

    adaptive_df["policy_name"] = "adaptive"
    adaptive_df["strategy"] = ranking_policy
    adaptive_df["threshold_used"] = base_threshold

    if "rank_score" not in adaptive_df.columns:
        adaptive_df["rank_score"] = adaptive_df["fraud_score"]

    if "expected_fraud_loss" not in adaptive_df.columns:
        adaptive_df["expected_fraud_loss"] = 0.0

    if "expected_investigation_cost" not in adaptive_df.columns:
        adaptive_df["expected_investigation_cost"] = 0.0

    if "expected_benefit" not in adaptive_df.columns:
        adaptive_df["expected_benefit"] = (
            adaptive_df["expected_fraud_loss"]
            - adaptive_df["expected_investigation_cost"]
        )

    return (
        adaptive_df,
        current_alert_rate,
    )


# =========================================================
# BATCH EVALUATION
# =========================================================
def evaluate_batch_results(
    df: pd.DataFrame,
    investigation_cost_per_alert: float,
    false_negative_factor: float,
) -> dict[str, Any]:
    """
    Calculate fraud-detection and operational metrics for a batch
    decision result.
    """
    required_columns = [
        "alert",
        "isFraud",
        "amount",
    ]

    missing_columns = [
        column
        for column in required_columns
        if column not in df.columns
    ]

    if missing_columns:
        raise ValueError(
            "Batch evaluation is missing required columns: "
            f"{missing_columns}"
        )

    if df.empty:
        raise ValueError(
            "Cannot evaluate an empty batch result."
        )

    if investigation_cost_per_alert < 0:
        raise ValueError(
            "investigation_cost_per_alert cannot be negative."
        )

    if false_negative_factor <= 0:
        raise ValueError(
            "false_negative_factor must be greater than 0."
        )

    alert_mask = (
        df["alert"]
        .fillna(0)
        .astype(int)
        .eq(1)
    )

    fraud_mask = (
        df["isFraud"]
        .fillna(0)
        .astype(int)
        .eq(1)
    )

    true_positive_mask = (
        alert_mask
        & fraud_mask
    )

    false_positive_mask = (
        alert_mask
        & (~fraud_mask)
    )

    missed_fraud_mask = (
        (~alert_mask)
        & fraud_mask
    )

    total_transactions = int(
        len(df)
    )

    total_frauds = int(
        fraud_mask.sum()
    )

    selected_alerts = int(
        alert_mask.sum()
    )

    frauds_detected = int(
        true_positive_mask.sum()
    )

    frauds_missed = int(
        missed_fraud_mask.sum()
    )

    false_positives = int(
        false_positive_mask.sum()
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

    investigation_cost_total = float(
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
                true_positive_mask,
                "amount",
            ]
            * false_negative_factor
        ).sum()
    )

    total_operational_cost = float(
        investigation_cost_total
        + missed_fraud_cost
    )

    return {
        "total_transactions": total_transactions,
        "total_frauds": total_frauds,
        "selected_alerts": selected_alerts,
        "frauds_detected": frauds_detected,
        "frauds_missed": frauds_missed,
        "false_positives": false_positives,
        "precision": round(
            precision,
            6,
        ),
        "recall": round(
            recall,
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


# =========================================================
# SEQUENTIAL INPUT
# =========================================================
def prepare_sequential_input(
    batch_df: pd.DataFrame,
    policy_name: str,
) -> pd.DataFrame:
    """
    Convert a completed batch policy into the generic input required
    by the Sequential Simulation.

    The Sequential Simulation does not create alerts. It receives
    already-created batch alerts through `policy_alert_candidate`.
    """
    required_columns = [
        "alert",
        "rank_score",
        "fraud_score",
        "step",
        "transaction_id",
        "simulation_entity_key",
        "amount",
        "isFraud",
    ]

    missing_columns = [
        column
        for column in required_columns
        if column not in batch_df.columns
    ]

    if missing_columns:
        raise ValueError(
            "Sequential input is missing required columns: "
            f"{missing_columns}"
        )

    sequential_df = batch_df.copy()

    sequential_df["policy_name"] = policy_name

    sequential_df["policy_alert_candidate"] = (
        sequential_df["alert"]
        .fillna(0)
        .astype(int)
        .eq(1)
    )

    sequential_df["rank_score"] = (
        sequential_df["rank_score"]
        .fillna(
            sequential_df["fraud_score"]
        )
    )

    return sequential_df


# =========================================================
# SEQUENTIAL EXECUTION
# =========================================================
def run_sequential_policy(
    batch_df: pd.DataFrame,
    policy_name: str,
    investigation_cost: float,
    false_negative_factor: float,
    alert_budget_per_step: int,
    suppression_window: int,
    monitoring_window_size: int,
) -> dict[str, Any]:
    """
    Run the policy-independent Sequential Simulation over an
    already-created batch policy.
    """
    sequential_input_df = (
        prepare_sequential_input(
            batch_df=batch_df,
            policy_name=policy_name,
        )
    )

    simulated_df = run_sequential_simulation(
        alerts_df=sequential_input_df,
        alert_budget_per_step=(
            alert_budget_per_step
        ),
        suppression_window=(
            suppression_window
        ),
    )

    summary = evaluate_sequential_results(
        df=simulated_df,
        investigation_cost_per_alert=(
            investigation_cost
        ),
        false_negative_factor=(
            false_negative_factor
        ),
    )

    operational_steps_df = build_operational_step_breakdown(
        df=simulated_df,
        alert_budget_per_step=alert_budget_per_step,
    )

    monitoring_df = build_monitoring_windows(
        df=simulated_df,
        investigation_cost_per_alert=(
            investigation_cost
        ),
        false_negative_factor=(
            false_negative_factor
        ),
        window_size=monitoring_window_size,
    )

    return {
        "summary": summary,
        "operational_steps": (
            operational_steps_df.to_dict(
                orient="records"
            )
        ),
        "monitoring_windows": (
            monitoring_df.to_dict(
                orient="records"
            )
        ),
    }


# =========================================================
# COMPARISON HELPERS
# =========================================================
def build_four_scenario_comparison(
    static_batch: dict[str, Any],
    static_sequential: dict[str, Any],
    adaptive_batch: dict[str, Any],
    adaptive_sequential: dict[str, Any],
) -> list[dict[str, Any]]:
    """
    Build one dashboard-ready comparison table containing all four
    scenarios.
    """
    return [
        {
            "scenario": "static_batch",
            "policy": "static",
            "evaluation_mode": "batch",
            **static_batch,
        },
        {
            "scenario": "static_sequential",
            "policy": "static",
            "evaluation_mode": "sequential",
            **static_sequential["summary"],
        },
        {
            "scenario": "adaptive_batch",
            "policy": "adaptive",
            "evaluation_mode": "batch",
            **adaptive_batch,
        },
        {
            "scenario": "adaptive_sequential",
            "policy": "adaptive",
            "evaluation_mode": "sequential",
            **adaptive_sequential["summary"],
        },
    ]


def build_difference_summary(
    first_summary: dict[str, Any],
    second_summary: dict[str, Any],
) -> dict[str, Any]:
    """
    Calculate the second scenario minus the first scenario.
    """
    return {
        "alert_difference": (
            second_summary["selected_alerts"]
            - first_summary["selected_alerts"]
        ),
        "frauds_detected_difference": (
            second_summary["frauds_detected"]
            - first_summary["frauds_detected"]
        ),
        "frauds_missed_difference": (
            second_summary["frauds_missed"]
            - first_summary["frauds_missed"]
        ),
        "recall_difference": round(
            second_summary["recall"]
            - first_summary["recall"],
            6,
        ),
        "precision_difference": round(
            second_summary["precision"]
            - first_summary["precision"],
            6,
        ),
        "operational_cost_difference": round(
            second_summary[
                "total_operational_cost"
            ]
            - first_summary[
                "total_operational_cost"
            ],
            2,
        ),
    }


def calculate_comparison_differences(
    static_batch: dict[str, Any],
    static_sequential: dict[str, Any],
    adaptive_batch: dict[str, Any],
    adaptive_sequential: dict[str, Any],
) -> dict[str, Any]:
    """
    Calculate within-policy and between-policy differences.
    """
    static_sequential_summary = (
        static_sequential["summary"]
    )

    adaptive_sequential_summary = (
        adaptive_sequential["summary"]
    )

    return {
        "static_batch_to_static_sequential": (
            build_difference_summary(
                first_summary=static_batch,
                second_summary=(
                    static_sequential_summary
                ),
            )
        ),
        "adaptive_batch_to_adaptive_sequential": (
            build_difference_summary(
                first_summary=adaptive_batch,
                second_summary=(
                    adaptive_sequential_summary
                ),
            )
        ),
        "static_batch_to_adaptive_batch": (
            build_difference_summary(
                first_summary=static_batch,
                second_summary=adaptive_batch,
            )
        ),
        "static_sequential_to_adaptive_sequential": (
            build_difference_summary(
                first_summary=(
                    static_sequential_summary
                ),
                second_summary=(
                    adaptive_sequential_summary
                ),
            )
        ),
    }


# =========================================================
# API ENDPOINT
# =========================================================
@router.get("/sequential")
def sequential_simulation(
    limit: int = Query(
        default=10000,
        ge=1,
        le=100000,
    ),
    investigation_cost: float = Query(
        default=10.0,
        ge=0.0,
    ),
    static_threshold: float = Query(
        default=0.5,
        ge=0.0,
        le=1.0,
    ),
    alert_rate_low: float = Query(
        default=0.03,
        ge=0.0,
        le=1.0,
    ),
    alert_rate_high: float = Query(
        default=0.10,
        ge=0.0,
        le=1.0,
    ),
    budget_multiplier: float = Query(
        default=1.4,
        ge=0.0,
    ),
    ranking_policy: str = Query(
        default="risk_zone",
    ),
    risk_zone_floor: float = Query(
        default=0.3,
        ge=0.0,
        le=1.0,
    ),
    alert_budget_per_step: int = Query(
        default=30,
        ge=1,
    ),
    suppression_window: int = Query(
        default=3,
        ge=0,
    ),
    monitoring_window_size: int = Query(
        default=1000,
        ge=1,
    ),
):
    """
    Run and compare:

    1. Static Batch
    2. Static Sequential
    3. Adaptive Batch
    4. Adaptive Sequential
    """
    try:
        if alert_rate_low > alert_rate_high:
            raise ValueError(
                "alert_rate_low cannot be greater than "
                "alert_rate_high."
            )

        config, _ = load_active_model()

        decision_config = config["decisioning"]

        false_negative_factor = float(
            decision_config[
                "cost_false_negative_factor"
            ]
        )

        # -----------------------------------------------------
        # COMMON SCORED DATA
        # -----------------------------------------------------
        base_df = prepare_base_data(
            limit=limit,
        )

        # -----------------------------------------------------
        # 1. STATIC BATCH
        # -----------------------------------------------------
        static_batch_df = run_static_batch(
            base_df=base_df,
            static_threshold=static_threshold,
            investigation_cost=investigation_cost,
        )

        static_batch_summary = (
            evaluate_batch_results(
                df=static_batch_df,
                investigation_cost_per_alert=(
                    investigation_cost
                ),
                false_negative_factor=(
                    false_negative_factor
                ),
            )
        )

        static_batch_alert_budget = int(
            static_batch_summary[
                "selected_alerts"
            ]
        )

        # -----------------------------------------------------
        # 2. ADAPTIVE BATCH
        # -----------------------------------------------------
        adaptive_alert_budget = calculate_alert_budget(
            static_alerts=static_batch_alert_budget,
            budget_multiplier=budget_multiplier,
        )

        (
            adaptive_batch_df,
            current_alert_rate,
        ) = run_adaptive_batch(
            base_df=base_df,
            base_threshold=static_threshold,
            adaptive_alert_budget=(
                adaptive_alert_budget
            ),
            investigation_cost=(
                investigation_cost
            ),
            ranking_policy=ranking_policy,
            risk_zone_floor=risk_zone_floor,
        )

        adaptive_batch_summary = (
            evaluate_batch_results(
                df=adaptive_batch_df,
                investigation_cost_per_alert=(
                    investigation_cost
                ),
                false_negative_factor=(
                    false_negative_factor
                ),
            )
        )

        # -----------------------------------------------------
        # 3. STATIC SEQUENTIAL
        # -----------------------------------------------------
        static_sequential_results = (
            run_sequential_policy(
                batch_df=static_batch_df,
                policy_name="static",
                investigation_cost=(
                    investigation_cost
                ),
                false_negative_factor=(
                    false_negative_factor
                ),
                alert_budget_per_step=(
                    alert_budget_per_step
                ),
                suppression_window=(
                    suppression_window
                ),
                monitoring_window_size=(
                    monitoring_window_size
                ),
            )
        )

        # -----------------------------------------------------
        # 4. ADAPTIVE SEQUENTIAL
        # -----------------------------------------------------
        adaptive_sequential_results = (
            run_sequential_policy(
                batch_df=adaptive_batch_df,
                policy_name="adaptive",
                investigation_cost=(
                    investigation_cost
                ),
                false_negative_factor=(
                    false_negative_factor
                ),
                alert_budget_per_step=(
                    alert_budget_per_step
                ),
                suppression_window=(
                    suppression_window
                ),
                monitoring_window_size=(
                    monitoring_window_size
                ),
            )
        )

        unique_steps = int(
            base_df["step"].nunique()
        )

        maximum_sequential_capacity = int(
            unique_steps
            * alert_budget_per_step
        )

        scenario_comparison = (
            build_four_scenario_comparison(
                static_batch=(
                    static_batch_summary
                ),
                static_sequential=(
                    static_sequential_results
                ),
                adaptive_batch=(
                    adaptive_batch_summary
                ),
                adaptive_sequential=(
                    adaptive_sequential_results
                ),
            )
        )

        comparison_differences = (
            calculate_comparison_differences(
                static_batch=(
                    static_batch_summary
                ),
                static_sequential=(
                    static_sequential_results
                ),
                adaptive_batch=(
                    adaptive_batch_summary
                ),
                adaptive_sequential=(
                    adaptive_sequential_results
                ),
            )
        )

        return {
            "parameters": {
                "limit": limit,
                "investigation_cost": (
                    investigation_cost
                ),
                "false_negative_factor": (
                    false_negative_factor
                ),
                "static_threshold": (
                    static_threshold
                ),
                "adaptive_policy": ranking_policy,
                "risk_zone_floor": risk_zone_floor,
                "current_alert_rate": round(
                    current_alert_rate,
                    6,
                ),
                "legacy_alert_rate_low": (
                    alert_rate_low
                ),
                "legacy_alert_rate_high": (
                    alert_rate_high
                ),
                "budget_multiplier": (
                    budget_multiplier
                ),
                "static_batch_alert_budget": (
                    static_batch_alert_budget
                ),
                "adaptive_batch_alert_budget": (
                    adaptive_alert_budget
                ),
                "alert_budget_per_step": (
                    alert_budget_per_step
                ),
                "suppression_window": (
                    suppression_window
                ),
                "monitoring_window_size": (
                    monitoring_window_size
                ),
                "unique_steps": (
                    unique_steps
                ),
                "maximum_sequential_capacity": (
                    maximum_sequential_capacity
                ),
                "unique_simulation_entities": int(
                    base_df[
                        "simulation_entity_key"
                    ].nunique()
                ),
            },
            "static_batch": {
                "summary": (
                    static_batch_summary
                ),
            },
            "static_sequential": (
                static_sequential_results
            ),
            "adaptive_batch": {
                "summary": (
                    adaptive_batch_summary
                ),
            },
            "adaptive_sequential": (
                adaptive_sequential_results
            ),
            "scenario_comparison": (
                scenario_comparison
            ),
            "comparison_differences": (
                comparison_differences
            ),
        }

    except FileNotFoundError as exc:
        raise HTTPException(
            status_code=404,
            detail=str(exc),
        ) from exc

    except KeyError as exc:
        raise HTTPException(
            status_code=500,
            detail=(
                "Missing configuration field: "
                f"{exc}"
            ),
        ) from exc

    except ValueError as exc:
        raise HTTPException(
            status_code=400,
            detail=str(exc),
        ) from exc

    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=(
                "Sequential simulation failed: "
                f"{exc}"
            ),
        ) from exc


# =========================================================
# SENSITIVITY ANALYSIS
# =========================================================
def _classify_policy_outcome(
    static_summary: dict[str, Any],
    adaptive_summary: dict[str, Any],
    tolerance: float = 1e-9,
) -> str:
    """Classify one Static-versus-Adaptive sensitivity result."""
    static_recall = float(static_summary.get("recall", 0.0))
    adaptive_recall = float(adaptive_summary.get("recall", 0.0))
    static_cost = float(static_summary.get("total_operational_cost", 0.0))
    adaptive_cost = float(adaptive_summary.get("total_operational_cost", 0.0))

    recall_difference = adaptive_recall - static_recall
    cost_difference = adaptive_cost - static_cost

    recall_equal = abs(recall_difference) <= tolerance
    cost_equal = abs(cost_difference) <= 0.01

    if recall_equal and cost_equal:
        return "tie"

    if recall_equal:
        return "adaptive" if adaptive_cost < static_cost else "static"

    if recall_difference > tolerance and adaptive_cost <= static_cost:
        return "adaptive"

    if recall_difference < -tolerance and static_cost <= adaptive_cost:
        return "static"

    return "trade_off"


def _build_sensitivity_row(
    experiment: str,
    api_parameter: str,
    tested_value: Any,
    static_summary: dict[str, Any],
    adaptive_summary: dict[str, Any],
) -> dict[str, Any]:
    """Create one dashboard-ready sensitivity result row."""
    static_recall = float(static_summary.get("recall", 0.0))
    adaptive_recall = float(adaptive_summary.get("recall", 0.0))
    static_cost = float(static_summary.get("total_operational_cost", 0.0))
    adaptive_cost = float(adaptive_summary.get("total_operational_cost", 0.0))

    return {
        "experiment": experiment,
        "api_parameter": api_parameter,
        "tested_value": tested_value,
        "static_selected_alerts": int(static_summary.get("selected_alerts", 0)),
        "adaptive_selected_alerts": int(adaptive_summary.get("selected_alerts", 0)),
        "static_frauds_detected": int(static_summary.get("frauds_detected", 0)),
        "adaptive_frauds_detected": int(adaptive_summary.get("frauds_detected", 0)),
        "static_frauds_missed": int(static_summary.get("frauds_missed", 0)),
        "adaptive_frauds_missed": int(adaptive_summary.get("frauds_missed", 0)),
        "static_precision": round(float(static_summary.get("precision", 0.0)), 6),
        "adaptive_precision": round(float(adaptive_summary.get("precision", 0.0)), 6),
        "static_recall": round(static_recall, 6),
        "adaptive_recall": round(adaptive_recall, 6),
        "recall_difference": round(adaptive_recall - static_recall, 6),
        "static_operational_cost": round(static_cost, 2),
        "adaptive_operational_cost": round(adaptive_cost, 2),
        "adaptive_cost_saving": round(static_cost - adaptive_cost, 2),
        "winner": _classify_policy_outcome(
            static_summary=static_summary,
            adaptive_summary=adaptive_summary,
        ),
        "status": "success",
    }


@router.get("/sensitivity")
def sensitivity_analysis(
    limit: int = Query(default=10000, ge=1, le=100000),
    investigation_cost: float = Query(default=10.0, ge=0.0),
    static_threshold: float = Query(default=0.5, ge=0.0, le=1.0),
    ranking_policy: str = Query(default="risk_zone"),
    risk_zone_floor: float = Query(default=0.3, ge=0.0, le=1.0),
    budget_multiplier: float = Query(default=1.4, ge=0.0),
    alert_budget_per_step: int = Query(default=50, ge=1),
    suppression_window: int = Query(default=3, ge=0),
    monitoring_window_size: int = Query(default=1000, ge=1),
):
    """
    Run all one-at-a-time sensitivity experiments in one API request.

    Expensive model loading, data loading and model scoring are reused across
    settings wherever possible. Each experiment changes one parameter while
    keeping the baseline values of all remaining parameters fixed.
    """
    try:
        config, _ = load_active_model()
        false_negative_factor = float(
            config["decisioning"]["cost_false_negative_factor"]
        )

        experiment_plan: list[dict[str, Any]] = [
            {
                "name": "Transaction volume",
                "parameter": "limit",
                "values": [1000, 3000, 10000, 50000],
            },
            {
                "name": "Analyst capacity",
                "parameter": "alert_budget_per_step",
                "values": list(range(10, 101, 10)),
            },
            {
                "name": "Investigation cost",
                "parameter": "investigation_cost",
                "values": [5.0, 10.0, 15.0, 20.0, 25.0],
            },
            {
                "name": "Suppression window",
                "parameter": "suppression_window",
                "values": [0, 1, 2, 3, 4, 5],
            },
            {
                "name": "Adaptive budget multiplier",
                "parameter": "budget_multiplier",
                "values": [round(value / 10, 1) for value in range(10, 21)],
            },
            {
                "name": "Static threshold",
                "parameter": "static_threshold",
                "values": [0.30, 0.40, 0.50, 0.60, 0.70],
            },
            {
                "name": "Minimum Adaptive threshold",
                "parameter": "risk_zone_floor",
                "values": [0.10, 0.20, 0.30, 0.40, 0.50],
            },
        ]

        baseline = {
            "limit": int(limit),
            "investigation_cost": float(investigation_cost),
            "static_threshold": float(static_threshold),
            "ranking_policy": ranking_policy,
            "risk_zone_floor": float(risk_zone_floor),
            "budget_multiplier": float(budget_multiplier),
            "alert_budget_per_step": int(alert_budget_per_step),
            "suppression_window": int(suppression_window),
            "monitoring_window_size": int(monitoring_window_size),
        }

        base_data_cache: dict[int, pd.DataFrame] = {}
        batch_cache: dict[tuple[Any, ...], tuple[pd.DataFrame, pd.DataFrame]] = {}
        sequential_cache: dict[tuple[Any, ...], tuple[dict[str, Any], dict[str, Any]]] = {}

        def get_base_data(current_limit: int) -> pd.DataFrame:
            if current_limit not in base_data_cache:
                base_data_cache[current_limit] = prepare_base_data(
                    limit=current_limit
                )
            return base_data_cache[current_limit]

        def get_batch_pair(
            settings: dict[str, Any],
        ) -> tuple[pd.DataFrame, pd.DataFrame]:
            key = (
                settings["limit"],
                settings["investigation_cost"],
                settings["static_threshold"],
                settings["ranking_policy"],
                settings["risk_zone_floor"],
                settings["budget_multiplier"],
            )

            if key in batch_cache:
                return batch_cache[key]

            base_df = get_base_data(settings["limit"])

            static_batch_df = run_static_batch(
                base_df=base_df,
                static_threshold=settings["static_threshold"],
                investigation_cost=settings["investigation_cost"],
            )

            static_alert_budget = int(
                static_batch_df["alert"].fillna(0).astype(int).sum()
            )
            adaptive_alert_budget = calculate_alert_budget(
                static_alerts=static_alert_budget,
                budget_multiplier=settings["budget_multiplier"],
            )

            adaptive_batch_df, _ = run_adaptive_batch(
                base_df=base_df,
                base_threshold=settings["static_threshold"],
                adaptive_alert_budget=adaptive_alert_budget,
                investigation_cost=settings["investigation_cost"],
                ranking_policy=settings["ranking_policy"],
                risk_zone_floor=settings["risk_zone_floor"],
            )

            batch_cache[key] = (static_batch_df, adaptive_batch_df)
            return batch_cache[key]

        def evaluate_setting(
            settings: dict[str, Any],
        ) -> tuple[dict[str, Any], dict[str, Any]]:
            key = (
                settings["limit"],
                settings["investigation_cost"],
                settings["static_threshold"],
                settings["ranking_policy"],
                settings["risk_zone_floor"],
                settings["budget_multiplier"],
                settings["alert_budget_per_step"],
                settings["suppression_window"],
            )

            if key in sequential_cache:
                return sequential_cache[key]

            static_batch_df, adaptive_batch_df = get_batch_pair(settings)

            static_result = run_sequential_policy(
                batch_df=static_batch_df,
                policy_name="static",
                investigation_cost=settings["investigation_cost"],
                false_negative_factor=false_negative_factor,
                alert_budget_per_step=settings["alert_budget_per_step"],
                suppression_window=settings["suppression_window"],
                monitoring_window_size=settings["monitoring_window_size"],
            )["summary"]

            adaptive_result = run_sequential_policy(
                batch_df=adaptive_batch_df,
                policy_name="adaptive",
                investigation_cost=settings["investigation_cost"],
                false_negative_factor=false_negative_factor,
                alert_budget_per_step=settings["alert_budget_per_step"],
                suppression_window=settings["suppression_window"],
                monitoring_window_size=settings["monitoring_window_size"],
            )["summary"]

            sequential_cache[key] = (static_result, adaptive_result)
            return sequential_cache[key]

        rows: list[dict[str, Any]] = []
        experiment_summaries: list[dict[str, Any]] = []

        for experiment in experiment_plan:
            experiment_rows: list[dict[str, Any]] = []

            for tested_value in experiment["values"]:
                settings = baseline.copy()
                settings[experiment["parameter"]] = tested_value

                static_summary, adaptive_summary = evaluate_setting(settings)
                row = _build_sensitivity_row(
                    experiment=experiment["name"],
                    api_parameter=experiment["parameter"],
                    tested_value=tested_value,
                    static_summary=static_summary,
                    adaptive_summary=adaptive_summary,
                )
                rows.append(row)
                experiment_rows.append(row)

            winner_counts = {
                "adaptive": sum(row["winner"] == "adaptive" for row in experiment_rows),
                "static": sum(row["winner"] == "static" for row in experiment_rows),
                "tie": sum(row["winner"] == "tie" for row in experiment_rows),
                "trade_off": sum(row["winner"] == "trade_off" for row in experiment_rows),
            }

            experiment_summaries.append(
                {
                    "experiment": experiment["name"],
                    "api_parameter": experiment["parameter"],
                    "tested_values": experiment["values"],
                    "tested_settings": len(experiment_rows),
                    **winner_counts,
                }
            )

        overall_counts = {
            "adaptive": sum(row["winner"] == "adaptive" for row in rows),
            "static": sum(row["winner"] == "static" for row in rows),
            "tie": sum(row["winner"] == "tie" for row in rows),
            "trade_off": sum(row["winner"] == "trade_off" for row in rows),
        }

        return {
            "method": "one-at-a-time parameter sensitivity",
            "baseline_parameters": baseline,
            "experiment_plan": experiment_plan,
            "overall_counts": overall_counts,
            "experiment_summaries": experiment_summaries,
            "results": rows,
            "execution_metadata": {
                "model_and_config_loads": 1,
                "scored_dataset_variants": sorted(base_data_cache.keys()),
                "scored_dataset_count": len(base_data_cache),
                "unique_batch_configurations": len(batch_cache),
                "unique_sequential_configurations": len(sequential_cache),
                "total_tested_settings": len(rows),
            },
        }

    except FileNotFoundError as exc:
        raise HTTPException(
            status_code=404,
            detail=str(exc),
        ) from exc
    except KeyError as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Missing configuration field: {exc}",
        ) from exc
    except ValueError as exc:
        raise HTTPException(
            status_code=400,
            detail=str(exc),
        ) from exc
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Sensitivity analysis failed: {exc}",
        ) from exc
