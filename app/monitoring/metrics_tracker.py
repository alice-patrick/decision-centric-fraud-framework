import json

from app.core.paths import LOGS_DIR


def read_jsonl_log(log_filename: str) -> list[dict]:
    log_path = LOGS_DIR / log_filename

    if not log_path.exists():
        return []

    records = []

    with open(log_path, "r", encoding="utf-8") as file:
        for line in file:
            if line.strip():
                records.append(json.loads(line))

    return records


def safe_average(values: list[float]) -> float:
    return sum(values) / len(values) if values else 0


def safe_divide(numerator: float, denominator: float) -> float:
    return numerator / denominator if denominator else 0


def calculate_monitoring_metrics(config: dict) -> dict:
    predictions = read_jsonl_log(config["logging"]["predictions_log_path"])
    alerts = read_jsonl_log(config["logging"]["alerts_log_path"])

    total_predictions = len(predictions)
    total_alerts = len(alerts)

    scores = [r["model"]["fraud_score"] for r in predictions]
    expected_losses = [r["decision"]["expected_fraud_loss"] for r in predictions]
    investigation_costs = [
        r["decision"]["expected_investigation_cost"] for r in predictions
    ]

    total_expected_fraud_loss = sum(expected_losses)
    total_investigation_cost = sum(investigation_costs)
    total_system_cost = total_expected_fraud_loss + total_investigation_cost

    alert_rate = safe_divide(total_alerts, total_predictions)

    return {
        "total_predictions": total_predictions,
        "total_alerts": total_alerts,
        "alert_rate": alert_rate,
        "alert_percentage": alert_rate * 100,
        "average_fraud_score": safe_average(scores),
        "average_expected_fraud_loss": safe_average(expected_losses),
        "average_investigation_cost": safe_average(investigation_costs),
        "total_expected_fraud_loss": total_expected_fraud_loss,
        "total_investigation_cost": total_investigation_cost,
        "total_system_cost": total_system_cost,
        "cost_per_alert": safe_divide(total_system_cost, total_alerts),
        "average_cost_per_transaction": safe_divide(
            total_system_cost, total_predictions
        ),
        "average_expected_loss_per_transaction": safe_divide(
            total_expected_fraud_loss, total_predictions
        ),
    }