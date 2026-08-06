import sys
from pathlib import Path

import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from app.core.config_loader import load_config
from app.core.registry import load_model_registry, get_active_model_info
from app.model.save_load import load_model
from app.model.predict import predict_proba

from decisioning.strategies import (
    StaticThresholdStrategy,
    StaticThresholdCappedStrategy,
    TopKStrategy,
    CostAwareStrategy,
    FullDecisionSystemStrategy,
)


def load_real_transactions(project_root: Path) -> pd.DataFrame:
    dataset_path = project_root / "data" / "raw" / "AIML Dataset.csv"

    if not dataset_path.exists():
        raise FileNotFoundError(f"Dataset not found: {dataset_path}")

    if dataset_path.stat().st_size == 0:
        raise ValueError(f"Dataset file is empty: {dataset_path}")

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

    missing_columns = [col for col in required_columns if col not in df.columns]
    if missing_columns:
        raise ValueError(f"Missing required columns: {missing_columns}")

    df = df[required_columns].copy()
    df = df.sort_values("step").reset_index(drop=True)

    # Synthetic entity groups for suppression testing.
    # Important: do NOT use nameOrig here because it is usually unique in PaySim.
    df["entity_id"] = (
        df["type"].astype(str)
        + "_"
        + df["amount"].round(-2).astype(int).astype(str)
    )

    return df


def add_scores(df: pd.DataFrame, model) -> pd.DataFrame:
    feature_cols = [
        "step",
        "type",
        "amount",
        "oldbalanceOrg",
        "newbalanceOrig",
        "oldbalanceDest",
        "newbalanceDest",
    ]

    missing_features = [col for col in feature_cols if col not in df.columns]
    if missing_features:
        raise ValueError(f"Missing model feature columns: {missing_features}")

    scores = []

    for _, row in df.iterrows():
        transaction = row[feature_cols].to_dict()
        score = predict_proba(model, transaction)
        scores.append(score)

    df = df.copy()
    df["fraud_score"] = scores

    return df


def evaluate_strategy(df: pd.DataFrame, alert_col: str, strategy_name: str) -> dict:
    required_columns = [alert_col, "isFraud", "amount"]

    missing_columns = [col for col in required_columns if col not in df.columns]
    if missing_columns:
        raise ValueError(f"Missing evaluation columns: {missing_columns}")

    alerts = df[df[alert_col] == 1]

    frauds_total = int(df["isFraud"].sum())
    alerts_count = int(len(alerts))
    frauds_caught = int(alerts["isFraud"].sum())
    false_positives = int(alerts_count - frauds_caught)
    missed_frauds = int(frauds_total - frauds_caught)

    precision = frauds_caught / alerts_count if alerts_count else 0
    recall = frauds_caught / frauds_total if frauds_total else 0
    alert_rate = alerts_count / len(df) if len(df) else 0

    missed_fraud_loss = df[
        (df["isFraud"] == 1) & (df[alert_col] == 0)
    ]["amount"].sum()

    investigation_cost = alerts_count * 50
    total_cost = missed_fraud_loss + investigation_cost

    suppressed_count = int(df["suppressed"].sum()) if "suppressed" in df.columns else 0
    suppression_rate = suppressed_count / len(df) if len(df) else 0

    return {
        "strategy": strategy_name,
        "transactions": len(df),
        "frauds_total": frauds_total,
        "alerts": alerts_count,
        "frauds_caught": frauds_caught,
        "missed_frauds": missed_frauds,
        "false_positives": false_positives,
        "precision_alerts": precision,
        "recall_fraud": recall,
        "alert_rate": alert_rate,
        "suppressed": suppressed_count,
        "suppression_rate": suppression_rate,
        "missed_fraud_loss": missed_fraud_loss,
        "investigation_cost": investigation_cost,
        "total_operational_cost": total_cost,
    }


def main():
    print(">>> DECISION STRATEGY EVALUATION RUNNING <<<")

    config = load_config()

    registry = load_model_registry(config["model"]["registry_path"])
    model_info = get_active_model_info(registry)
    model = load_model(model_info["path"])

    df = load_real_transactions(PROJECT_ROOT).head(10000)
    df = add_scores(df, model)

    decision_cfg = config["decisioning"]

    static_threshold = decision_cfg["static_threshold"]
    false_positive_cost = decision_cfg["cost_false_positive"]
    false_negative_factor = decision_cfg["cost_false_negative_factor"]

    alert_budget = max(1, int(len(df) * 0.02))

    print(f"\nTransactions evaluated: {len(df)}")
    print(f"Alert budget: {alert_budget}")
    print(f"Static threshold: {static_threshold}")
    print(f"False positive cost: {false_positive_cost}")
    print(f"False negative factor: {false_negative_factor}")
    print(f"Unique entities: {df['entity_id'].nunique()}")

    strategies = [
        (
            StaticThresholdStrategy(
                threshold=static_threshold,
                decision_col="alert_static_threshold",
            ),
            "alert_static_threshold",
            "static_threshold",
        ),
        (
            StaticThresholdCappedStrategy(
                threshold=static_threshold,
                k=alert_budget,
                decision_col="alert_static_capped",
            ),
            "alert_static_capped",
            "static_threshold_capped",
        ),
        (
            TopKStrategy(
                k=alert_budget,
                decision_col="alert_top_k",
            ),
            "alert_top_k",
            "top_k_adaptive",
        ),
        (
            CostAwareStrategy(
                k=alert_budget,
                false_positive_cost=false_positive_cost,
                false_negative_factor=false_negative_factor,
                decision_col="alert_cost_aware",
            ),
            "alert_cost_aware",
            "cost_aware_ranking",
        ),
        (
            FullDecisionSystemStrategy(
                k=alert_budget,
                false_positive_cost=false_positive_cost,
                false_negative_factor=false_negative_factor,
                decision_col="alert_full_system",
                entity_col="entity_id",
            ),
            "alert_full_system",
            "full_decision_system",
        ),
    ]

    results = []

    for strategy, alert_col, strategy_name in strategies:
        df_strategy = strategy.select(df)
        metrics = evaluate_strategy(df_strategy, alert_col, strategy_name)
        results.append(metrics)

    results_df = pd.DataFrame(results)

    print("\nSTRATEGY COMPARISON")
    print(results_df.to_string(index=False))

    output_path = PROJECT_ROOT / "logs" / "decision_strategy_comparison.csv"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    results_df.to_csv(output_path, index=False)

    print(f"\nSaved results to: {output_path}")


if __name__ == "__main__":
    main()