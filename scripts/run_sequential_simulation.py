import sys
from pathlib import Path

import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))


from app.core.config_loader import load_config
from app.core.registry import (
    get_active_model_info,
    load_model_registry,
)
from app.model.predict import predict_proba
from app.model.save_load import load_model
from decisioning.ranking import (
    calculate_expected_fraud_loss,
    calculate_expected_investigation_cost,
    calculate_rank_score,
)


def load_real_transactions(
    project_root: Path,
) -> pd.DataFrame:
    dataset_path = (
        project_root
        / "data"
        / "raw"
        / "AIML Dataset.csv"
    )

    if not dataset_path.exists():
        raise FileNotFoundError(
            f"Dataset not found: {dataset_path}"
        )

    df = pd.read_csv(dataset_path)

    required_columns = [
        "step",
        "type",
        "amount",
        "oldbalanceOrg",
        "newbalanceOrig",
        "oldbalanceDest",
        "newbalanceDest",
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

    df = df[required_columns].copy()
    df = df.sort_values("step").reset_index(drop=True)

    df["transaction_id"] = df.index

    # Simulation proxy only.
    # This is not a real customer, account, or card identifier.
    df["simulation_entity_key"] = (
        df["type"].astype(str)
        + "_"
        + df["amount"]
        .round(-2)
        .astype(int)
        .astype(str)
    )

    return df


def add_scores(
    df: pd.DataFrame,
    model,
    investigation_cost: float,
    false_negative_factor: float,
) -> pd.DataFrame:
    feature_columns = [
        "step",
        "type",
        "amount",
        "oldbalanceOrg",
        "newbalanceOrig",
        "oldbalanceDest",
        "newbalanceDest",
    ]

    scores = []

    for _, row in df.iterrows():
        transaction = row[feature_columns].to_dict()
        score = predict_proba(model, transaction)
        scores.append(score)

    df = df.copy()
    df["fraud_score"] = scores

    df["expected_fraud_loss"] = (
        calculate_expected_fraud_loss(
            fraud_score=df["fraud_score"],
            amount=df["amount"],
            false_negative_factor=false_negative_factor,
        )
    )

    df["expected_investigation_cost"] = (
        calculate_expected_investigation_cost(
            fraud_score=df["fraud_score"],
            investigation_cost=investigation_cost,
        )
    )

    df["expected_benefit"] = (
        df["expected_fraud_loss"]
        - df["expected_investigation_cost"]
    )

    df["rank_score"] = calculate_rank_score(
        fraud_score=df["fraud_score"],
        amount=df["amount"],
        investigation_cost=investigation_cost,
        false_negative_factor=false_negative_factor,
    )

    return df


def run_sequential_simulation(
    df: pd.DataFrame,
    alert_budget_per_step: int,
    suppression_window: int,
) -> pd.DataFrame:
    if alert_budget_per_step <= 0:
        raise ValueError(
            "alert_budget_per_step must be greater than 0."
        )

    if suppression_window < 0:
        raise ValueError(
            "suppression_window cannot be negative."
        )

    required_columns = [
        "step",
        "rank_score",
        "simulation_entity_key",
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

    results = []
    recent_entities: dict[str, int] = {}

    for step, step_df in df.groupby("step", sort=True):
        step_df = step_df.copy()

        step_df["decision"] = 0
        step_df["suppressed"] = 0
        step_df["strategy"] = (
            "sequential_budget_aware_selection"
        )

        expired_entities = [
            entity_key
            for entity_key, last_seen_step
            in recent_entities.items()
            if step - last_seen_step > suppression_window
        ]

        for entity_key in expired_entities:
            del recent_entities[entity_key]

        step_df = step_df.sort_values(
            "rank_score",
            ascending=False,
        )

        alerts_used = 0

        for index, row in step_df.iterrows():
            if alerts_used >= alert_budget_per_step:
                break

            entity_key = row["simulation_entity_key"]

            if entity_key in recent_entities:
                step_df.at[index, "suppressed"] = 1
                continue

            step_df.at[index, "decision"] = 1
            recent_entities[entity_key] = int(step)
            alerts_used += 1

        results.append(step_df)

    if not results:
        return df.copy()

    return (
        pd.concat(results)
        .sort_index()
        .reset_index(drop=True)
    )


def safe_divide(
    numerator: float,
    denominator: float,
) -> float:
    return numerator / denominator if denominator else 0.0


def evaluate_sequential_results(
    df: pd.DataFrame,
    investigation_cost_per_alert: float,
) -> dict:
    required_columns = [
        "decision",
        "suppressed",
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
            f"Missing required columns: {missing_columns}"
        )

    alerts = df[df["decision"] == 1]

    frauds_total = int(df["isFraud"].sum())
    alerts_count = int(len(alerts))
    frauds_caught = int(alerts["isFraud"].sum())

    missed_frauds_df = df[
        (df["isFraud"] == 1)
        & (df["decision"] == 0)
    ]

    missed_frauds = int(len(missed_frauds_df))
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

    missed_fraud_loss = float(
        missed_frauds_df["amount"].sum()
    )

    fraud_loss_prevented = float(
        alerts.loc[
            alerts["isFraud"] == 1,
            "amount",
        ].sum()
    )

    investigation_cost_total = float(
        alerts_count * investigation_cost_per_alert
    )

    total_operational_cost = (
        missed_fraud_loss
        + investigation_cost_total
    )

    suppressed_count = int(
        df["suppressed"].sum()
    )

    suppression_rate = safe_divide(
        suppressed_count,
        len(df),
    )

    return {
        "strategy": (
            "sequential_budget_aware_selection"
        ),
        "transactions": int(len(df)),
        "frauds_total": frauds_total,
        "alerts": alerts_count,
        "frauds_caught": frauds_caught,
        "missed_frauds": missed_frauds,
        "false_positives": false_positives,
        "precision": precision,
        "recall": recall,
        "alert_rate": alert_rate,
        "suppressed": suppressed_count,
        "suppression_rate": suppression_rate,
        "missed_fraud_loss": missed_fraud_loss,
        "fraud_loss_prevented": fraud_loss_prevented,
        "investigation_cost_total": (
            investigation_cost_total
        ),
        "total_operational_cost": (
            total_operational_cost
        ),
    }


def build_monitoring_windows(
    df: pd.DataFrame,
    investigation_cost_per_alert: float,
    window_size: int = 1000,
) -> pd.DataFrame:
    if window_size <= 0:
        raise ValueError(
            "window_size must be greater than 0."
        )

    monitoring_rows = []

    for start in range(0, len(df), window_size):
        window = df.iloc[
            start:start + window_size
        ]

        metrics = evaluate_sequential_results(
            window,
            investigation_cost_per_alert=(
                investigation_cost_per_alert
            ),
        )

        metrics["window_start"] = start
        metrics["window_end"] = (
            start + len(window) - 1
        )

        monitoring_rows.append(metrics)

    return pd.DataFrame(monitoring_rows)


def main() -> None:
    print(
        ">>> SEQUENTIAL SIMULATION RUNNING <<<"
    )

    config = load_config()

    registry = load_model_registry(
        config["model"]["registry_path"]
    )

    model_info = get_active_model_info(registry)
    model = load_model(model_info["path"])

    decision_config = config["decisioning"]

    investigation_cost = decision_config[
        "cost_false_positive"
    ]

    false_negative_factor = decision_config[
        "cost_false_negative_factor"
    ]

    df = load_real_transactions(
        PROJECT_ROOT
    ).head(10000)

    df = add_scores(
        df=df,
        model=model,
        investigation_cost=investigation_cost,
        false_negative_factor=(
            false_negative_factor
        ),
    )

    alert_budget_per_step = 30
    suppression_window = 3

    print(
        f"\nTransactions evaluated: {len(df)}"
    )

    print(
        f"Unique steps: {df['step'].nunique()}"
    )

    print(
        "Unique simulation entities: "
        f"{df['simulation_entity_key'].nunique()}"
    )

    print(
        "Alert budget per step: "
        f"{alert_budget_per_step}"
    )

    print(
        "Suppression window: "
        f"{suppression_window} steps"
    )

    print(
        f"Investigation cost: {investigation_cost}"
    )

    print(
        "False negative factor: "
        f"{false_negative_factor}"
    )

    simulated_df = run_sequential_simulation(
        df=df,
        alert_budget_per_step=(
            alert_budget_per_step
        ),
        suppression_window=suppression_window,
    )

    summary = evaluate_sequential_results(
        simulated_df,
        investigation_cost_per_alert=(
            investigation_cost
        ),
    )

    summary_df = pd.DataFrame([summary])

    print(
        "\nSEQUENTIAL SIMULATION SUMMARY"
    )

    print(
        summary_df.to_string(index=False)
    )

    monitoring_df = build_monitoring_windows(
        simulated_df,
        investigation_cost_per_alert=(
            investigation_cost
        ),
        window_size=1000,
    )

    print("\nMONITORING WINDOWS")

    monitoring_columns = [
        "window_start",
        "window_end",
        "alerts",
        "frauds_caught",
        "precision",
        "recall",
        "suppressed",
        "total_operational_cost",
    ]

    print(
        monitoring_df[
            monitoring_columns
        ].to_string(index=False)
    )

    output_summary_path = (
        PROJECT_ROOT
        / "logs"
        / "sequential_simulation_summary.csv"
    )

    output_monitoring_path = (
        PROJECT_ROOT
        / "logs"
        / "sequential_monitoring_windows.csv"
    )

    output_summary_path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    summary_df.to_csv(
        output_summary_path,
        index=False,
    )

    monitoring_df.to_csv(
        output_monitoring_path,
        index=False,
    )

    print(
        f"\nSaved summary to: "
        f"{output_summary_path}"
    )

    print(
        "Saved monitoring windows to: "
        f"{output_monitoring_path}"
    )


if __name__ == "__main__":
    main()