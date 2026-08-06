import pandas as pd

from decisioning.ranking import (
    calculate_expected_fraud_loss,
    calculate_expected_investigation_cost,
    calculate_rank_score,
)


def apply_ranking(
    df: pd.DataFrame,
    policy: str,
    investigation_cost: float,
    false_negative_factor: float = 1.0,
) -> pd.DataFrame:
    """
    Add cost-aware ranking fields to transaction data.
    """
    required_columns = {
        "fraud_score",
        "amount",
    }

    missing_columns = required_columns.difference(
        df.columns
    )

    if missing_columns:
        raise ValueError(
            "Missing required ranking columns: "
            f"{sorted(missing_columns)}"
        )

    if investigation_cost < 0:
        raise ValueError(
            "investigation_cost must be non-negative."
        )

    if false_negative_factor <= 0:
        raise ValueError(
            "false_negative_factor must be greater than 0."
        )

    ranked_df = df.copy()

    ranked_df["expected_fraud_loss"] = (
        calculate_expected_fraud_loss(
            fraud_score=ranked_df["fraud_score"],
            amount=ranked_df["amount"],
            false_negative_factor=false_negative_factor,
        )
    )

    ranked_df["expected_investigation_cost"] = (
        calculate_expected_investigation_cost(
            fraud_score=ranked_df["fraud_score"],
            investigation_cost=investigation_cost,
        )
    )

    ranked_df["expected_benefit"] = (
        ranked_df["expected_fraud_loss"]
        - ranked_df["expected_investigation_cost"]
    )

    if policy == "score":
        ranked_df["rank_score"] = (
            ranked_df["fraud_score"]
        )

    elif policy == "benefit":
        ranked_df["rank_score"] = (
            ranked_df["expected_benefit"]
        )

    elif policy == "hybrid":
        score_rank = ranked_df[
            "fraud_score"
        ].rank(pct=True)

        benefit_rank = ranked_df[
            "expected_benefit"
        ].rank(pct=True)

        ranked_df["rank_score"] = (
            0.5 * score_rank
            + 0.5 * benefit_rank
        )

    elif policy == "risk_zone":
        ranked_df["rank_score"] = (
            calculate_rank_score(
                fraud_score=ranked_df["fraud_score"],
                amount=ranked_df["amount"],
                investigation_cost=investigation_cost,
                false_negative_factor=(
                    false_negative_factor
                ),
            )
        )

    else:
        raise ValueError(
            "Unknown policy. Use one of: "
            "score, benefit, hybrid, risk_zone."
        )

    return ranked_df


def assign_severity_by_percentile(
    df: pd.DataFrame,
) -> pd.DataFrame:
    """
    Assign severity according to rank-score percentile.
    """
    result_df = df.copy()
    result_df["severity"] = "NONE"

    alerts_df = result_df[
        result_df["alert"] == 1
    ].copy()

    if alerts_df.empty:
        return result_df

    critical_cutoff = alerts_df[
        "rank_score"
    ].quantile(0.99)

    high_cutoff = alerts_df[
        "rank_score"
    ].quantile(0.85)

    medium_cutoff = alerts_df[
        "rank_score"
    ].quantile(0.60)

    result_df.loc[
        (
            (result_df["alert"] == 1)
            & (
                result_df["rank_score"]
                >= critical_cutoff
            )
        ),
        "severity",
    ] = "CRITICAL"

    result_df.loc[
        (
            (result_df["alert"] == 1)
            & (
                result_df["rank_score"]
                < critical_cutoff
            )
            & (
                result_df["rank_score"]
                >= high_cutoff
            )
        ),
        "severity",
    ] = "HIGH"

    result_df.loc[
        (
            (result_df["alert"] == 1)
            & (
                result_df["rank_score"]
                < high_cutoff
            )
            & (
                result_df["rank_score"]
                >= medium_cutoff
            )
        ),
        "severity",
    ] = "MEDIUM"

    result_df.loc[
        (
            (result_df["alert"] == 1)
            & (
                result_df["rank_score"]
                < medium_cutoff
            )
        ),
        "severity",
    ] = "LOW"

    return result_df


def build_reason(
    row: pd.Series,
) -> str:
    """
    Generate a human-readable explanation for the analyst queue.
    """
    if row["alert"] != 1:
        return "No alert generated"

    if row["severity"] == "CRITICAL":
        return (
            "Top 1% operational risk by rank score; "
            "immediate analyst escalation"
        )

    if row["severity"] == "HIGH":
        return (
            "High-priority alert selected by risk "
            "ranking and expected benefit"
        )

    if row["severity"] == "MEDIUM":
        return (
            "Medium-priority alert selected within "
            "analyst capacity"
        )

    return (
        "Low-priority risk-zone alert selected "
        "within available budget"
    )


def add_operational_fields(
    df: pd.DataFrame,
) -> pd.DataFrame:
    """
    Add severity, analyst priority and explanation fields.
    """
    result_df = assign_severity_by_percentile(df)

    result_df["reason"] = result_df.apply(
        build_reason,
        axis=1,
    )

    result_df["analyst_priority"] = (
        result_df["severity"].map(
            {
                "CRITICAL": 1,
                "HIGH": 2,
                "MEDIUM": 3,
                "LOW": 4,
                "NONE": 5,
            }
        )
    )

    return result_df


def run_static(
    df: pd.DataFrame,
    threshold: float,
    investigation_cost: float,
) -> pd.DataFrame:
    """
    Apply the static fraud-score threshold baseline.
    """
    static_df = apply_ranking(
        df=df,
        policy="risk_zone",
        investigation_cost=investigation_cost,
    )

    static_df["alert"] = (
        static_df["fraud_score"] >= threshold
    ).astype(int)

    static_df = add_operational_fields(
        static_df
    )

    return static_df


def run_decision_system(
    df: pd.DataFrame,
    investigation_cost: float,
    alert_budget: int,
    policy: str,
    risk_zone_floor: float = 0.3,
) -> pd.DataFrame:
    """
    Apply budget-aware alert selection.
    """
    if alert_budget < 0:
        raise ValueError(
            "alert_budget must be non-negative."
        )

    if not 0 <= risk_zone_floor <= 1:
        raise ValueError(
            "risk_zone_floor must be between 0 and 1."
        )

    decision_df = apply_ranking(
        df=df,
        policy=policy,
        investigation_cost=investigation_cost,
    )

    decision_df["alert"] = 0

    if alert_budget == 0:
        return add_operational_fields(
            decision_df
        )

    if policy == "risk_zone":
        candidate_df = decision_df[
            (
                decision_df["fraud_score"]
                >= risk_zone_floor
            )
            & (
                decision_df["expected_benefit"]
                > 0
            )
        ].copy()

        selected_indices = (
            candidate_df
            .sort_values(
                "rank_score",
                ascending=False,
            )
            .head(alert_budget)
            .index
        )

    else:
        selected_indices = (
            decision_df
            .sort_values(
                "rank_score",
                ascending=False,
            )
            .head(alert_budget)
            .index
        )

    decision_df.loc[
        selected_indices,
        "alert",
    ] = 1

    decision_df = add_operational_fields(
        decision_df
    )

    return decision_df