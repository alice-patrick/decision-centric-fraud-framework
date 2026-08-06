import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from app.core.config_loader import load_config
from decisioning.decision_engine import make_decision


def main():
    print(">>> DECISION ENGINE SCRIPT RUNNING <<<")

    config = load_config()

    test_cases = [
        {"score": 0.10, "amount": 50, "mode": "static", "label": "low score, low amount"},
        {"score": 0.10, "amount": 10_000, "mode": "static", "label": "low score, high amount"},
        {"score": 0.60, "amount": 50, "mode": "static", "label": "high score, low amount"},
        {"score": 0.50, "amount": 50, "mode": "adaptive", "current_alert_rate": 0.15, "label": "adaptive high alert pressure"},
        {"score": 0.50, "amount": 50, "mode": "adaptive", "current_alert_rate": 0.01, "label": "adaptive low alert pressure"},
    ]

    for case in test_cases:
        result = make_decision(
            score=case["score"],
            amount=case["amount"],
            config=config,
            mode=case["mode"],
            current_alert_rate=case.get("current_alert_rate"),
        )

        print(f"\nCASE: {case['label']}")
        print(f"score={result['score']:.2f}, amount={result['amount']}")
        print(f"mode={result['mode']}")
        print(f"threshold_used={result['threshold_used']:.2f}")
        print(f"base_decision={result['base_decision']}")
        print(f"cost_decision={result['cost_decision']}")
        print(f"final_decision={result['final_decision']}")
        print(f"decision={result['decision']}")
        print(f"reason={result['reason']}")
        print(f"expected_fraud_loss={result['expected_fraud_loss']:.4f}")
        print(f"expected_investigation_cost={result['expected_investigation_cost']:.4f}")


if __name__ == "__main__":
    main()