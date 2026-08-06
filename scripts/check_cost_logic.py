import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from app.core.config_loader import load_config
from decisioning.thresholding import apply_static_threshold
from decisioning.cost_logic import apply_cost_aware_decision


def main():
    print(">>> COST-AWARE LOGIC SCRIPT RUNNING <<<")

    config = load_config()
    decision_cfg = config["decisioning"]

    test_cases = [
        {"score": 0.10, "amount": 50, "label": "low score, low amount"},
        {"score": 0.10, "amount": 10_000, "label": "low score, high amount"},
        {"score": 0.60, "amount": 50, "label": "high score, low amount"},
        {"score": 0.60, "amount": 10_000, "label": "high score, high amount"},
    ]

    for case in test_cases:
        score = case["score"]
        amount = case["amount"]

        base_decision = apply_static_threshold(
            score=score,
            threshold=decision_cfg["static_threshold"],
        )

        final_decision, details = apply_cost_aware_decision(
            score=score,
            amount=amount,
            base_decision=base_decision,
            false_positive_cost=decision_cfg["cost_false_positive"],
            false_negative_factor=decision_cfg["cost_false_negative_factor"],
        )

        print(f"\nCASE: {case['label']}")
        print(f"score={score:.2f}, amount={amount}")
        print(f"base_decision={base_decision}")
        print(f"expected_fraud_loss={details['expected_fraud_loss']:.4f}")
        print(f"expected_investigation_cost={details['expected_investigation_cost']:.4f}")
        print(f"cost_decision={details['cost_decision']}")
        print(f"final_decision={final_decision}")


if __name__ == "__main__":
    main()