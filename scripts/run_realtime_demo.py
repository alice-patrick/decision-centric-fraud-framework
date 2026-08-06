import sys
import time
from pathlib import Path

import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from app.core.config_loader import load_config
from app.core.registry import load_model_registry, get_active_model_info
from app.model.save_load import load_model
from app.model.predict import predict_proba


def load_transactions(project_root: Path) -> pd.DataFrame:
    path = project_root / "data" / "raw" / "AIML Dataset.csv"

    if not path.exists():
        raise FileNotFoundError(f"Dataset not found: {path}")

    df = pd.read_csv(path)

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

    missing = [col for col in required_columns if col not in df.columns]
    if missing:
        raise ValueError(f"Missing columns: {missing}")

    df = df[required_columns].copy()
    df = df.sort_values("step").reset_index(drop=True)

    df["transaction_id"] = df.index

    df["entity_id"] = (
        df["type"].astype(str)
        + "_"
        + df["amount"].round(-2).astype(int).astype(str)
    )

    return df


def calculate_decision(
    score: float,
    amount: float,
    false_positive_cost: float,
    false_negative_factor: float,
) -> dict:
    expected_fraud_loss = score * amount * false_negative_factor
    expected_investigation_cost = (1 - score) * false_positive_cost
    rank_score = expected_fraud_loss - expected_investigation_cost

    return {
        "expected_fraud_loss": expected_fraud_loss,
        "expected_investigation_cost": expected_investigation_cost,
        "rank_score": rank_score,
    }


def main():
    print(">>> REAL-TIME FRAUD DECISION SYSTEM DEMO <<<")

    config = load_config()

    registry = load_model_registry(config["model"]["registry_path"])
    model_info = get_active_model_info(registry)
    model = load_model(model_info["path"])

    decision_cfg = config["decisioning"]

    false_positive_cost = decision_cfg["cost_false_positive"]
    false_negative_factor = decision_cfg["cost_false_negative_factor"]

    df = load_transactions(PROJECT_ROOT).head(300)

    alert_budget_per_step = 10
    suppression_window = 3
    sleep_seconds = 0.00

    recent_entities = {}
    alerts_used_by_step = {}

    total_transactions = 0
    total_alerts = 0
    frauds_caught = 0
    false_positives = 0
    suppressed_count = 0

    print(f"\nLoaded transactions: {len(df)}")
    print(f"Alert budget per step: {alert_budget_per_step}")
    print(f"Suppression window: {suppression_window}")
    print("-" * 90)

    feature_cols = [
        "step",
        "type",
        "amount",
        "oldbalanceOrg",
        "newbalanceOrig",
        "oldbalanceDest",
        "newbalanceDest",
    ]

    for _, row in df.iterrows():
        total_transactions += 1

        step = int(row["step"])
        entity_id = row["entity_id"]
        transaction_id = int(row["transaction_id"])

        alerts_used_by_step.setdefault(step, 0)

        expired_entities = [
            entity
            for entity, last_seen_step in recent_entities.items()
            if step - last_seen_step > suppression_window
        ]

        for entity in expired_entities:
            del recent_entities[entity]

        transaction = row[feature_cols].to_dict()
        score = predict_proba(model, transaction)

        decision_info = calculate_decision(
            score=score,
            amount=row["amount"],
            false_positive_cost=false_positive_cost,
            false_negative_factor=false_negative_factor,
        )

        cost_justified = (
            decision_info["expected_fraud_loss"]
            > decision_info["expected_investigation_cost"]
        )

        budget_available = alerts_used_by_step[step] < alert_budget_per_step
        suppressed = entity_id in recent_entities

        alert = cost_justified and budget_available and not suppressed

        if suppressed and cost_justified:
            suppressed_count += 1

        if alert:
            alerts_used_by_step[step] += 1
            recent_entities[entity_id] = step
            total_alerts += 1

            if row["isFraud"] == 1:
                frauds_caught += 1
                label = "TRUE FRAUD"
            else:
                false_positives += 1
                label = "FALSE POSITIVE"

            print(
                f"[ALERT] step={step} | tx={transaction_id} | "
                f"type={row['type']} | amount={row['amount']:.2f} | "
                f"score={score:.4f} | "
                f"rank_score={decision_info['rank_score']:.2f} | "
                f"{label}"
            )

        else:
            if total_transactions % 50 == 0:
                print(
                    f"[STATUS] processed={total_transactions} | "
                    f"alerts={total_alerts} | "
                    f"frauds_caught={frauds_caught} | "
                    f"suppressed={suppressed_count}"
                )

        if sleep_seconds > 0:
            time.sleep(sleep_seconds)

    frauds_total = int(df["isFraud"].sum())
    missed_frauds = frauds_total - frauds_caught

    precision = frauds_caught / total_alerts if total_alerts else 0
    recall = frauds_caught / frauds_total if frauds_total else 0

    missed_fraud_loss = df[
        (df["isFraud"] == 1)
    ]["amount"].sum()

    print("-" * 90)
    print("\nREAL-TIME DEMO SUMMARY")
    print(f"Transactions processed: {total_transactions}")
    print(f"Frauds total: {frauds_total}")
    print(f"Alerts generated: {total_alerts}")
    print(f"Frauds caught: {frauds_caught}")
    print(f"Missed frauds: {missed_frauds}")
    print(f"False positives: {false_positives}")
    print(f"Suppressed alerts: {suppressed_count}")
    print(f"Alert precision: {precision:.4f}")
    print(f"Fraud recall: {recall:.4f}")


if __name__ == "__main__":
    main()