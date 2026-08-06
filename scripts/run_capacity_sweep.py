"""
Run a capacity-sensitivity experiment against the FastAPI sequential simulation.

The script changes only `alert_budget_per_step`, while keeping all other
parameters fixed. It compares Static Sequential and Adaptive Sequential,
exports the results to CSV, and creates two figures:

1. Recall by analyst capacity
2. Operational cost by analyst capacity

Run from the project root while Uvicorn is active on port 8002:

    py scripts/run_capacity_sweep.py

Optional examples:

    py scripts/run_capacity_sweep.py --start 10 --stop 150 --step 10
    py scripts/run_capacity_sweep.py --capacities 20 30 40 50 60 70 80 90 100
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Any

import matplotlib.pyplot as plt
import pandas as pd
import requests


API_URL = "http://127.0.0.1:8002/simulation/sequential"

DEFAULT_PARAMS: dict[str, Any] = {
    "limit": 10000,
    "investigation_cost": 10.0,
    "static_threshold": 0.5,
    "ranking_policy": "risk_zone",
    "risk_zone_floor": 0.3,
    "alert_rate_low": 0.03,
    "alert_rate_high": 0.10,
    "budget_multiplier": 1.4,
    "suppression_window": 3,
    "monitoring_window_size": 1000,
}


def safe_float(value: Any, default: float = 0.0) -> float:
    try:
        if value is None:
            return default
        return float(value)
    except (TypeError, ValueError):
        return default


def safe_int(value: Any, default: int = 0) -> int:
    try:
        if value is None:
            return default
        return int(round(float(value)))
    except (TypeError, ValueError):
        return default


def first_present(mapping: dict[str, Any], *keys: str, default: Any = 0) -> Any:
    for key in keys:
        if key in mapping and mapping[key] is not None:
            return mapping[key]
    return default


def get_summary(payload: dict[str, Any], scenario_key: str) -> dict[str, Any]:
    scenario = payload.get(scenario_key, {})
    if not isinstance(scenario, dict):
        return {}

    summary = scenario.get("summary", {})
    if isinstance(summary, dict):
        return summary

    return {}


def determine_winner(
    static_recall: float,
    adaptive_recall: float,
    static_cost: float,
    adaptive_cost: float,
    tolerance: float = 1e-12,
) -> str:
    recall_diff = adaptive_recall - static_recall
    cost_diff = adaptive_cost - static_cost

    adaptive_better_recall = recall_diff > tolerance
    static_better_recall = recall_diff < -tolerance
    adaptive_lower_cost = cost_diff < -tolerance
    static_lower_cost = cost_diff > tolerance

    if adaptive_better_recall and adaptive_lower_cost:
        return "Adaptive dominates"
    if static_better_recall and static_lower_cost:
        return "Static dominates"
    if abs(recall_diff) <= tolerance and abs(cost_diff) <= tolerance:
        return "Tie"
    if adaptive_better_recall:
        return "Adaptive higher recall"
    if static_better_recall:
        return "Static higher recall"
    if adaptive_lower_cost:
        return "Adaptive lower cost"
    if static_lower_cost:
        return "Static lower cost"

    return "Mixed"


def run_one_capacity(capacity: int, timeout: int = 180) -> dict[str, Any]:
    params = {
        **DEFAULT_PARAMS,
        "alert_budget_per_step": int(capacity),
    }

    response = requests.get(API_URL, params=params, timeout=timeout)
    response.raise_for_status()
    payload = response.json()

    static = get_summary(payload, "static_sequential")
    adaptive = get_summary(payload, "adaptive_sequential")

    if not static or not adaptive:
        available_keys = ", ".join(sorted(payload.keys()))
        raise KeyError(
            "The API response did not contain both "
            "'static_sequential.summary' and 'adaptive_sequential.summary'. "
            f"Available top-level keys: {available_keys}"
        )

    static_alerts = safe_int(
        first_present(static, "selected_alerts", "alerts", default=0)
    )
    adaptive_alerts = safe_int(
        first_present(adaptive, "selected_alerts", "alerts", default=0)
    )

    static_frauds = safe_int(
        first_present(static, "frauds_detected", "frauds_caught", default=0)
    )
    adaptive_frauds = safe_int(
        first_present(adaptive, "frauds_detected", "frauds_caught", default=0)
    )

    static_missed = safe_int(
        first_present(static, "frauds_missed", "missed_frauds", default=0)
    )
    adaptive_missed = safe_int(
        first_present(adaptive, "frauds_missed", "missed_frauds", default=0)
    )

    static_recall = safe_float(first_present(static, "recall", default=0.0))
    adaptive_recall = safe_float(first_present(adaptive, "recall", default=0.0))

    static_precision = safe_float(first_present(static, "precision", default=0.0))
    adaptive_precision = safe_float(first_present(adaptive, "precision", default=0.0))

    static_cost = safe_float(
        first_present(static, "total_operational_cost", default=0.0)
    )
    adaptive_cost = safe_float(
        first_present(adaptive, "total_operational_cost", default=0.0)
    )

    static_candidates = safe_int(
        first_present(static, "policy_candidate_alerts", "candidate_alerts", default=0)
    )
    adaptive_candidates = safe_int(
        first_present(adaptive, "policy_candidate_alerts", "candidate_alerts", default=0)
    )

    static_rejected = safe_int(
        first_present(
            static,
            "capacity_rejected_alerts",
            "capacity_rejected",
            default=0,
        )
    )
    adaptive_rejected = safe_int(
        first_present(
            adaptive,
            "capacity_rejected_alerts",
            "capacity_rejected",
            default=0,
        )
    )

    static_suppressed = safe_int(
        first_present(static, "suppressed_alerts", "suppressed", default=0)
    )
    adaptive_suppressed = safe_int(
        first_present(adaptive, "suppressed_alerts", "suppressed", default=0)
    )

    recall_difference = adaptive_recall - static_recall
    cost_difference = adaptive_cost - static_cost

    return {
        "capacity_per_step": capacity,
        "static_candidate_alerts": static_candidates,
        "adaptive_candidate_alerts": adaptive_candidates,
        "static_accepted_alerts": static_alerts,
        "adaptive_accepted_alerts": adaptive_alerts,
        "static_capacity_rejected": static_rejected,
        "adaptive_capacity_rejected": adaptive_rejected,
        "static_suppressed": static_suppressed,
        "adaptive_suppressed": adaptive_suppressed,
        "static_frauds_detected": static_frauds,
        "adaptive_frauds_detected": adaptive_frauds,
        "static_frauds_missed": static_missed,
        "adaptive_frauds_missed": adaptive_missed,
        "static_precision": static_precision,
        "adaptive_precision": adaptive_precision,
        "static_recall": static_recall,
        "adaptive_recall": adaptive_recall,
        "recall_difference": recall_difference,
        "static_operational_cost": static_cost,
        "adaptive_operational_cost": adaptive_cost,
        "cost_difference_adaptive_minus_static": cost_difference,
        "cost_saving_adaptive_vs_static": static_cost - adaptive_cost,
        "winner": determine_winner(
            static_recall,
            adaptive_recall,
            static_cost,
            adaptive_cost,
        ),
    }


def create_recall_chart(results: pd.DataFrame, output_path: Path) -> None:
    plt.figure(figsize=(10, 6))
    plt.plot(
        results["capacity_per_step"],
        results["static_recall"],
        marker="o",
        label="Static Sequential",
    )
    plt.plot(
        results["capacity_per_step"],
        results["adaptive_recall"],
        marker="o",
        label="Adaptive Sequential",
    )
    plt.xlabel("Alerts allowed per time step")
    plt.ylabel("Recall")
    plt.title("Sequential recall by analyst capacity")
    plt.legend()
    plt.grid(True, alpha=0.3)
    plt.tight_layout()
    plt.savefig(output_path, dpi=200)
    plt.close()


def create_difference_chart(results: pd.DataFrame, output_path: Path) -> None:
    plt.figure(figsize=(10, 6))
    plt.axhline(0.0, linewidth=1)
    plt.plot(
        results["capacity_per_step"],
        results["recall_difference"],
        marker="o",
    )
    plt.xlabel("Alerts allowed per time step")
    plt.ylabel("Adaptive recall − Static recall")
    plt.title("Adaptive recall advantage by analyst capacity")
    plt.grid(True, alpha=0.3)
    plt.tight_layout()
    plt.savefig(output_path, dpi=200)
    plt.close()


def create_cost_chart(results: pd.DataFrame, output_path: Path) -> None:
    plt.figure(figsize=(10, 6))
    plt.plot(
        results["capacity_per_step"],
        results["static_operational_cost"],
        marker="o",
        label="Static Sequential",
    )
    plt.plot(
        results["capacity_per_step"],
        results["adaptive_operational_cost"],
        marker="o",
        label="Adaptive Sequential",
    )
    plt.xlabel("Alerts allowed per time step")
    plt.ylabel("Total operational cost (€)")
    plt.title("Sequential operational cost by analyst capacity")
    plt.legend()
    plt.grid(True, alpha=0.3)
    plt.tight_layout()
    plt.savefig(output_path, dpi=200)
    plt.close()


def print_summary(results: pd.DataFrame) -> None:
    adaptive_recall_wins = int((results["recall_difference"] > 0).sum())
    static_recall_wins = int((results["recall_difference"] < 0).sum())
    recall_ties = int((results["recall_difference"] == 0).sum())

    adaptive_cost_wins = int(
        (results["cost_difference_adaptive_minus_static"] < 0).sum()
    )
    static_cost_wins = int(
        (results["cost_difference_adaptive_minus_static"] > 0).sum()
    )
    cost_ties = int(
        (results["cost_difference_adaptive_minus_static"] == 0).sum()
    )

    print("\nCapacity sweep completed.\n")
    print(
        results[
            [
                "capacity_per_step",
                "static_recall",
                "adaptive_recall",
                "recall_difference",
                "static_operational_cost",
                "adaptive_operational_cost",
                "winner",
            ]
        ].to_string(index=False)
    )

    print("\nRecall comparison:")
    print(f"  Adaptive wins: {adaptive_recall_wins}")
    print(f"  Static wins:   {static_recall_wins}")
    print(f"  Ties:          {recall_ties}")

    print("\nOperational-cost comparison:")
    print(f"  Adaptive lower cost: {adaptive_cost_wins}")
    print(f"  Static lower cost:   {static_cost_wins}")
    print(f"  Ties:                {cost_ties}")

    best_row = results.loc[results["recall_difference"].idxmax()]
    worst_row = results.loc[results["recall_difference"].idxmin()]

    print("\nLargest Adaptive recall advantage:")
    print(
        f"  Capacity {int(best_row['capacity_per_step'])}: "
        f"{best_row['recall_difference']:+.2%}"
    )

    print("\nLargest Adaptive recall disadvantage:")
    print(
        f"  Capacity {int(worst_row['capacity_per_step'])}: "
        f"{worst_row['recall_difference']:+.2%}"
    )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run Static vs Adaptive Sequential capacity sensitivity analysis."
    )

    parser.add_argument(
        "--capacities",
        nargs="+",
        type=int,
        help="Explicit capacity values, e.g. --capacities 10 20 30 40 50",
    )
    parser.add_argument("--start", type=int, default=10)
    parser.add_argument("--stop", type=int, default=150)
    parser.add_argument("--step", type=int, default=10)
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("metrics") / "capacity_sweep",
    )

    return parser.parse_args()


def main() -> int:
    args = parse_args()

    if args.capacities:
        capacities = sorted(set(args.capacities))
    else:
        if args.step <= 0:
            raise ValueError("--step must be greater than zero.")
        if args.stop < args.start:
            raise ValueError("--stop must be greater than or equal to --start.")
        capacities = list(range(args.start, args.stop + 1, args.step))

    if not capacities or any(value < 1 for value in capacities):
        raise ValueError("All capacity values must be positive integers.")

    output_dir: Path = args.output_dir
    output_dir.mkdir(parents=True, exist_ok=True)

    rows: list[dict[str, Any]] = []

    print(f"API endpoint: {API_URL}")
    print(f"Capacities: {capacities}\n")

    for capacity in capacities:
        print(f"Running capacity {capacity}...", end=" ", flush=True)

        try:
            row = run_one_capacity(capacity)
        except requests.exceptions.ConnectionError:
            print("FAILED")
            print(
                "\nFastAPI is not available. Start it in another terminal:\n"
                "py -m uvicorn app.api.main:app --reload --port 8002"
            )
            return 1
        except requests.exceptions.Timeout:
            print("FAILED")
            print(
                f"\nThe API timed out at capacity {capacity}. "
                "Try a smaller transaction limit or increase the timeout."
            )
            return 1
        except requests.exceptions.HTTPError as error:
            print("FAILED")
            print(f"\nFastAPI returned HTTP error at capacity {capacity}: {error}")
            if error.response is not None:
                print(error.response.text)
            return 1
        except (KeyError, ValueError) as error:
            print("FAILED")
            print(f"\nCould not parse the API response: {error}")
            return 1

        rows.append(row)
        print(
            f"Static recall={row['static_recall']:.2%}, "
            f"Adaptive recall={row['adaptive_recall']:.2%}, "
            f"Difference={row['recall_difference']:+.2%}"
        )

    results = pd.DataFrame(rows).sort_values("capacity_per_step")

    csv_path = output_dir / "capacity_sweep_results.csv"
    recall_chart_path = output_dir / "capacity_vs_recall.png"
    difference_chart_path = output_dir / "capacity_vs_recall_difference.png"
    cost_chart_path = output_dir / "capacity_vs_operational_cost.png"

    results.to_csv(csv_path, index=False)

    create_recall_chart(results, recall_chart_path)
    create_difference_chart(results, difference_chart_path)
    create_cost_chart(results, cost_chart_path)

    print_summary(results)

    print("\nFiles created:")
    print(f"  {csv_path}")
    print(f"  {recall_chart_path}")
    print(f"  {difference_chart_path}")
    print(f"  {cost_chart_path}")

    return 0


if __name__ == "__main__":
    sys.exit(main())