import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from app.core.config_loader import load_config
from app.core.registry import load_model_registry, get_active_model_info
from app.model.save_load import load_model
from app.model.predict import predict_proba
from decisioning.decision_engine import make_decision


def main():
    print(">>> END-TO-END DECISION SCRIPT RUNNING <<<")

    config = load_config()

    registry = load_model_registry(config["model"]["registry_path"])
    model_info = get_active_model_info(registry)
    model = load_model(model_info["path"])

    transaction = {
        "step": 1,
        "type": "TRANSFER",
        "amount": 10_000,
        "oldbalanceOrg": 10_000,
        "newbalanceOrig": 0,
        "oldbalanceDest": 0,
        "newbalanceDest": 10_000,
    }

    score = predict_proba(model, transaction)

    result = make_decision(
        score=score,
        amount=transaction["amount"],
        config=config,
        mode="adaptive",
        current_alert_rate=0.05,
    )

    print("\nTRANSACTION INPUT")
    for key, value in transaction.items():
        print(f"{key}: {value}")

    print("\nMODEL OUTPUT")
    print(f"fraud_score={score:.8f}")

    print("\nDECISION OUTPUT")
    print("-" * 40)
    print(f"mode: {result['mode']}")
    print(f"threshold_used: {result['threshold_used']:.4f}")
    print(f"base_decision: {result['base_decision']}")
    print(f"cost_decision: {result['cost_decision']}")
    print(f"final_decision: {result['final_decision']}")
    print(f"decision: {result['decision']}")
    print(f"reason: {result['reason']}")
    print(f"expected_fraud_loss: {result['expected_fraud_loss']:.4f}")
    print(f"expected_investigation_cost: {result['expected_investigation_cost']:.4f}")
    print("-" * 40)

    print("\nSUMMARY")
    print("=" * 40)
    print(
        f"Decision: {result['decision'].upper()} | "
        f"Score: {score:.4f} | "
        f"Threshold: {result['threshold_used']:.4f} | "
        f"Expected Loss: {result['expected_fraud_loss']:.2f} | "
        f"Investigation Cost: {result['expected_investigation_cost']:.2f}"
    )
    print("=" * 40)

if __name__ == "__main__":
    main()