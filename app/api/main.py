import sys
from pathlib import Path

import pandas as pd
from fastapi import FastAPI
from fastapi.responses import RedirectResponse

PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT))

from app.services.analyst_queue_service import (
    build_analyst_queue,
    get_selected_alerts,
)
from app.services.data_service import load_data
from app.services.decision_service import (
    run_decision_system,
    run_static,
)
from app.services.metrics_service import (
    build_business_kpis,
    evaluate,
)
from app.services.model_service import (
    load_active_model,
    score_data,
)
from app.services.operating_curve_service import (
    build_operating_curve,
    calculate_alert_budget,
)


from app.api.simulation import (
    router as simulation_router,
)


app = FastAPI(
    title="Fraud Decision System API",
    docs_url="/docs",
    redoc_url="/redoc",
)


app.include_router(simulation_router)


ALERT_COLUMNS = [
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
]


EXPORT_COLUMNS = [
    "transaction_id",
    "step",
    "type",
    "amount",
    "fraud_score",
    "rank_score",
    "expected_benefit",
    "expected_investigation_cost",
    "static_alert",
    "adaptive_alert",
    "adaptive_gain_fraud",
    "alert",
    "selected_for_review",
    "queue_position",
    "budget_overflow",
    "severity",
    "analyst_priority",
    "reason",
    "isFraud",
]


def prepare_scored_data(
    limit: int,
) -> tuple[dict, pd.DataFrame]:
    """
    Load the active model, transaction data
    and fraud probability scores.
    """
    config, model = load_active_model()

    df = load_data(
        project_root=PROJECT_ROOT,
        limit=limit,
    )

    scored_df = score_data(
        df=df,
        model=model,
    )

    return config, scored_df


def prepare_static_baseline(
    df: pd.DataFrame,
    threshold: float,
    investigation_cost: float,
) -> tuple[pd.DataFrame, int, dict]:
    """
    Run the static-threshold baseline and calculate
    its alert volume and evaluation metrics.
    """
    static_df = run_static(
        df=df,
        threshold=threshold,
        investigation_cost=investigation_cost,
    )

    static_alerts = int(
        static_df["alert"].sum()
    )

    static_metrics = evaluate(
        df=static_df,
        alert_col="alert",
        investigation_cost=investigation_cost,
    )

    return (
        static_df,
        static_alerts,
        static_metrics,
    )


def prepare_decision_run(
    df: pd.DataFrame,
    threshold: float,
    investigation_cost: float,
    ranking_policy: str,
    risk_zone_floor: float,
    budget_multiplier: float,
) -> tuple[
    pd.DataFrame,
    pd.DataFrame,
    int,
    int,
    dict,
    dict,
]:
    """
    Prepare both the static baseline and the
    adaptive decision-system results.
    """
    (
        static_df,
        static_alerts,
        static_metrics,
    ) = prepare_static_baseline(
        df=df,
        threshold=threshold,
        investigation_cost=investigation_cost,
    )

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

    return (
        static_df,
        decision_df,
        static_alerts,
        decision_budget,
        static_metrics,
        decision_metrics,
    )


def add_export_comparison_columns(
    static_df: pd.DataFrame,
    decision_df: pd.DataFrame,
) -> pd.DataFrame:
    """
    Add transaction-level comparison fields used
    by the decision-export endpoint.
    """
    export_df = decision_df.copy()

    export_df["static_alert"] = (
        static_df["alert"].values
    )

    export_df["adaptive_alert"] = (
        export_df["alert"]
    )

    export_df["adaptive_gain_fraud"] = (
        (
            export_df["static_alert"] == 0
        )
        & (
            export_df["adaptive_alert"] == 1
        )
        & (
            export_df["isFraud"] == 1
        )
    ).astype(int)

    return export_df


@app.get(
    "/",
    include_in_schema=False,
)
def root():
    """
    Redirect the root URL to the Swagger documentation.
    """
    return RedirectResponse("/docs")


@app.get("/comparison")
def comparison(
    limit: int = 10000,
    investigation_cost: float = 10,
    ranking_policy: str = "risk_zone",
    risk_zone_floor: float = 0.3,
    budget_multiplier: float = 1.4,
):
    """
    Compare the static-threshold baseline with
    the adaptive and budget-aware decision system.
    """
    config, df = prepare_scored_data(
        limit=limit,
    )

    threshold = config[
        "decisioning"
    ][
        "static_threshold"
    ]

    (
        _,
        _,
        static_alerts,
        decision_budget,
        static_metrics,
        decision_metrics,
    ) = prepare_decision_run(
        df=df,
        threshold=threshold,
        investigation_cost=investigation_cost,
        ranking_policy=ranking_policy,
        risk_zone_floor=risk_zone_floor,
        budget_multiplier=budget_multiplier,
    )

    business_kpis = build_business_kpis(
        static_metrics=static_metrics,
        decision_metrics=decision_metrics,
    )

    return {
        "parameters": {
            "limit": limit,
            "investigation_cost": investigation_cost,
            "ranking_policy": ranking_policy,
            "risk_zone_floor": risk_zone_floor,
            "static_threshold": threshold,
            "static_alert_budget": static_alerts,
            "decision_budget": decision_budget,
            "budget_multiplier": budget_multiplier,
        },
        "static": static_metrics,
        "decision_system": decision_metrics,
        "business_kpis": business_kpis,
        "cost_diff": (
            decision_metrics[
                "total_operational_cost"
            ]
            - static_metrics[
                "total_operational_cost"
            ]
        ),
        "recall_diff": (
            decision_metrics["recall"]
            - static_metrics["recall"]
        ),
        "precision_diff": (
            decision_metrics["precision"]
            - static_metrics["precision"]
        ),
        "missed_fraud_cost_diff": (
            decision_metrics[
                "missed_fraud_cost"
            ]
            - static_metrics[
                "missed_fraud_cost"
            ]
        ),
        "fraud_loss_prevented_diff": (
            decision_metrics[
                "fraud_loss_prevented"
            ]
            - static_metrics[
                "fraud_loss_prevented"
            ]
        ),
    }


@app.get("/alerts")
def alerts(
    limit: int = 10000,
    investigation_cost: float = 10,
    ranking_policy: str = "risk_zone",
    risk_zone_floor: float = 0.3,
    budget_multiplier: float = 1.4,
    analyst_capacity: int = 250,
):
    """
    Return the prioritised alerts selected
    for analyst review.
    """
    config, df = prepare_scored_data(
        limit=limit,
    )

    threshold = config[
        "decisioning"
    ][
        "static_threshold"
    ]

    (
        _,
        decision_df,
        _,
        _,
        _,
        _,
    ) = prepare_decision_run(
        df=df,
        threshold=threshold,
        investigation_cost=investigation_cost,
        ranking_policy=ranking_policy,
        risk_zone_floor=risk_zone_floor,
        budget_multiplier=budget_multiplier,
    )

    queue_df = build_analyst_queue(
        df=decision_df,
        analyst_capacity=analyst_capacity,
    )

    selected_df = get_selected_alerts(
        df=queue_df,
        limit=analyst_capacity,
    )

    return selected_df[
        ALERT_COLUMNS
    ].to_dict(
        orient="records",
    )


@app.get("/decision_export")
def decision_export(
    limit: int = 10000,
    investigation_cost: float = 10,
    ranking_policy: str = "risk_zone",
    risk_zone_floor: float = 0.3,
    budget_multiplier: float = 1.4,
    analyst_capacity: int = 250,
):
    """
    Export transaction-level decisions and
    analyst-queue information for analytics.
    """
    config, df = prepare_scored_data(
        limit=limit,
    )

    threshold = config[
        "decisioning"
    ][
        "static_threshold"
    ]

    (
        static_df,
        decision_df,
        _,
        _,
        _,
        _,
    ) = prepare_decision_run(
        df=df,
        threshold=threshold,
        investigation_cost=investigation_cost,
        ranking_policy=ranking_policy,
        risk_zone_floor=risk_zone_floor,
        budget_multiplier=budget_multiplier,
    )

    export_df = add_export_comparison_columns(
        static_df=static_df,
        decision_df=decision_df,
    )

    queue_df = build_analyst_queue(
        df=export_df,
        analyst_capacity=analyst_capacity,
    )

    return queue_df[
        EXPORT_COLUMNS
    ].to_dict(
        orient="records",
    )


@app.get("/operating_curve")
def operating_curve(
    limit: int = 10000,
    investigation_cost: float = 10,
    ranking_policy: str = "risk_zone",
    risk_zone_floor: float = 0.3,
):
    """
    Evaluate the decision system across
    multiple alert-budget multipliers.
    """
    config, df = prepare_scored_data(
        limit=limit,
    )

    threshold = config[
        "decisioning"
    ][
        "static_threshold"
    ]

    (
        _,
        static_alerts,
        static_metrics,
    ) = prepare_static_baseline(
        df=df,
        threshold=threshold,
        investigation_cost=investigation_cost,
    )

    rows = build_operating_curve(
        df=df,
        static_metrics=static_metrics,
        static_alerts=static_alerts,
        investigation_cost=investigation_cost,
        ranking_policy=ranking_policy,
        risk_zone_floor=risk_zone_floor,
    )

    return {
        "parameters": {
            "limit": limit,
            "investigation_cost": investigation_cost,
            "ranking_policy": ranking_policy,
            "risk_zone_floor": risk_zone_floor,
            "static_threshold": threshold,
            "static_alerts": static_alerts,
        },
        "static_baseline": static_metrics,
        "operating_curve": rows,
    }