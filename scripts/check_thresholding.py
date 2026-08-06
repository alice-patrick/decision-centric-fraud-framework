import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from app.core.config_loader import load_config
from decisioning.thresholding import (
    apply_static_threshold,
    apply_adaptive_threshold,
)


def main():
    print(">>> THRESHOLDING SCRIPT RUNNING <<<")

    config = load_config()
    decision_cfg = config["decisioning"]

    scores = [0.01, 0.20, 0.49, 0.50, 0.75, 0.95]

    print("\nSTATIC THRESHOLD TEST")
    for score in scores:
        decision = apply_static_threshold(
            score=score,
            threshold=decision_cfg["static_threshold"]
        )
        print(f"score={score:.2f} -> alert={decision}")

    print("\nADAPTIVE THRESHOLD TEST")
    test_alert_rates = [0.01, 0.05, 0.15]

    for alert_rate in test_alert_rates:
        decision, threshold_used = apply_adaptive_threshold(
            score=0.50,
            base_threshold=decision_cfg["static_threshold"],
            current_alert_rate=alert_rate,
            alert_rate_low=decision_cfg["alert_rate_low"],
            alert_rate_high=decision_cfg["alert_rate_high"],
        )

        print(
            f"alert_rate={alert_rate:.2f} | "
            f"threshold_used={threshold_used:.2f} | "
            f"score=0.50 -> alert={decision}"
        )


if __name__ == "__main__":
    main()