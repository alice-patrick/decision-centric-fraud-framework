from __future__ import annotations

import argparse
import time
from pathlib import Path
from typing import Any

import matplotlib.pyplot as plt
import pandas as pd
import requests


API_BASE_URL = "http://127.0.0.1:8002"
SIMULATION_ENDPOINT = "simulation/sequential"

PROJECT_ROOT = Path(__file__).resolve().parents[1]
OUTPUT_DIR = PROJECT_ROOT / "metrics" / "robustness_analysis"

BASE_PARAMS: dict[str, Any] = {
    "limit": 10_000,
    "investigation_cost": 10.0,
    "static_threshold": 0.5,
    "ranking_policy": "risk_zone",
    "risk_zone_floor": 0.3,
    "alert_rate_low": 0.03,
    "alert_rate_high": 0.10,
    "budget_multiplier": 1.4,
    "alert_budget_per_step": 50,
    "suppression_window": 3,
    "monitoring_window_size": 1_000,
}

# One-factor-at-a-time sensitivity analysis.
# Every experiment changes only one parameter while all others stay fixed.
EXPERIMENTS: dict[str, dict[str, Any]] = {
    "analyst_capacity": {
        "api_parameter": "alert_budget_per_step",
        "values": list(range(10, 151, 10)),
    },
    "transaction_volume": {
        "api_parameter": "limit",
        "values": [1_000, 3_000, 10_000, 50_000],
    },
    "investigation_cost": {
        "api_parameter": "investigation_cost",
        "values": [5.0, 10.0, 20.0, 50.0, 100.0],
    },
    "suppression_window": {
        "api_parameter": "suppression_window",
        "values": [0, 1, 3, 5, 10],
    },
    "budget_multiplier": {
        "api_parameter": "budget_multiplier",
        "values": [1.0, 1.1, 1.2, 1.3, 1.4, 1.5, 1.6],
    },
    "static_threshold": {
        "api_parameter": "static_threshold",
        "values": [0.3, 0.4, 0.5, 0.6, 0.7],
    },
}


def get_summary(payload: dict[str, Any], policy_key: str) -> dict[str, Any]:
    """Return the summary object for one sequential policy."""
    return payload.get(policy_key, {}).get("summary", {})


def as_float(value: Any, default: float = 0.0) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def as_int(value: Any, default: int = 0) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def call_api(
    session: requests.Session,
    api_base_url: str,
    params: dict[str, Any],
    timeout: int,
) -> dict[str, Any]:
    url = f"{api_base_url.rstrip('/')}/{SIMULATION_ENDPOINT}"

    response = session.get(
        url,
        params=params,
        timeout=timeout,
    )
    response.raise_for_status()
    return response.json()


def classify_result(
    static_recall: float,
    adaptive_recall: float,
    static_cost: float,
    adaptive_cost: float,
    tolerance: float = 1e-12,
) -> str:
    """
    Use Pareto-style comparison.

    Adaptive wins:
        Adaptive is no worse on recall and cost, and better on at least one.

    Static wins:
        Static is no worse on recall and cost, and better on at least one.

    Tie:
        Recall and cost are effectively equal.

    Trade-off:
        One policy has higher recall while the other has lower cost.
    """
    recall_diff = adaptive_recall - static_recall
    cost_diff = adaptive_cost - static_cost

    recall_equal = abs(recall_diff) <= tolerance
    cost_equal = abs(cost_diff) <= tolerance

    if recall_equal and cost_equal:
        return "Tie"

    adaptive_no_worse = recall_diff >= -tolerance and cost_diff <= tolerance
    adaptive_strictly_better = recall_diff > tolerance or cost_diff < -tolerance

    static_no_worse = recall_diff <= tolerance and cost_diff >= -tolerance
    static_strictly_better = recall_diff < -tolerance or cost_diff > tolerance

    if adaptive_no_worse and adaptive_strictly_better:
        return "Adaptive"

    if static_no_worse and static_strictly_better:
        return "Static"

    return "Trade-off"


def run_experiment(
    session: requests.Session,
    experiment_name: str,
    api_parameter: str,
    values: list[int | float],
    base_params: dict[str, Any],
    api_base_url: str,
    timeout: int,
    pause_seconds: float,
) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []

    print(f"\n{'=' * 72}")
    print(f"Experiment: {experiment_name}")
    print(f"API parameter: {api_parameter}")
    print(f"{'=' * 72}")

    for index, value in enumerate(values, start=1):
        params = {
            **base_params,
            api_parameter: value,
        }

        print(
            f"[{index:>2}/{len(values)}] "
            f"{api_parameter}={value} ... ",
            end="",
            flush=True,
        )

        try:
            payload = call_api(
                session=session,
                api_base_url=api_base_url,
                params=params,
                timeout=timeout,
            )

            static = get_summary(payload, "static_sequential")
            adaptive = get_summary(payload, "adaptive_sequential")

            static_recall = as_float(static.get("recall"))
            adaptive_recall = as_float(adaptive.get("recall"))

            static_precision = as_float(static.get("precision"))
            adaptive_precision = as_float(adaptive.get("precision"))

            static_cost = as_float(static.get("total_operational_cost"))
            adaptive_cost = as_float(adaptive.get("total_operational_cost"))

            winner = classify_result(
                static_recall=static_recall,
                adaptive_recall=adaptive_recall,
                static_cost=static_cost,
                adaptive_cost=adaptive_cost,
            )

            row = {
                "experiment": experiment_name,
                "api_parameter": api_parameter,
                "parameter_value": value,
                "static_recall": static_recall,
                "adaptive_recall": adaptive_recall,
                "recall_difference": adaptive_recall - static_recall,
                "static_precision": static_precision,
                "adaptive_precision": adaptive_precision,
                "precision_difference": adaptive_precision - static_precision,
                "static_operational_cost": static_cost,
                "adaptive_operational_cost": adaptive_cost,
                "adaptive_cost_saving": static_cost - adaptive_cost,
                "static_alerts_accepted": as_int(
                    static.get("alerts_accepted")
                    or static.get("accepted_alerts")
                ),
                "adaptive_alerts_accepted": as_int(
                    adaptive.get("alerts_accepted")
                    or adaptive.get("accepted_alerts")
                ),
                "static_frauds_caught": as_int(
                    static.get("frauds_caught")
                    or static.get("true_positives")
                ),
                "adaptive_frauds_caught": as_int(
                    adaptive.get("frauds_caught")
                    or adaptive.get("true_positives")
                ),
                "winner": winner,
                "status": "success",
                "error": "",
            }

            print(
                f"Static recall={static_recall:.2%}, "
                f"Adaptive recall={adaptive_recall:.2%}, "
                f"winner={winner}"
            )

        except requests.RequestException as exc:
            row = {
                "experiment": experiment_name,
                "api_parameter": api_parameter,
                "parameter_value": value,
                "winner": "Error",
                "status": "error",
                "error": str(exc),
            }
            print(f"ERROR: {exc}")

        rows.append(row)

        if pause_seconds > 0:
            time.sleep(pause_seconds)

    return pd.DataFrame(rows)


def build_conclusion(
    adaptive_wins: int,
    static_wins: int,
    ties: int,
    trade_offs: int,
) -> str:
    total_valid = adaptive_wins + static_wins + ties + trade_offs

    if total_valid == 0:
        return "No valid results"

    if adaptive_wins > static_wins and adaptive_wins >= max(1, total_valid // 2):
        return "Adaptive usually better"

    if static_wins > adaptive_wins and static_wins >= max(1, total_valid // 2):
        return "Static usually better"

    if ties == total_valid:
        return "Policies equivalent"

    if trade_offs >= max(adaptive_wins, static_wins, ties):
        return "Performance-cost trade-off"

    if adaptive_wins > static_wins:
        return "Adaptive advantage, but condition-dependent"

    if static_wins > adaptive_wins:
        return "Static advantage, but condition-dependent"

    return "Mixed / condition-dependent"


def summarise_experiment(frame: pd.DataFrame) -> dict[str, Any]:
    valid = frame.loc[frame["status"].eq("success")].copy()

    adaptive_wins = int(valid["winner"].eq("Adaptive").sum())
    static_wins = int(valid["winner"].eq("Static").sum())
    ties = int(valid["winner"].eq("Tie").sum())
    trade_offs = int(valid["winner"].eq("Trade-off").sum())
    errors = int(frame["status"].eq("error").sum())

    return {
        "parameter_tested": frame["experiment"].iloc[0],
        "adaptive_wins": adaptive_wins,
        "static_wins": static_wins,
        "ties": ties,
        "trade_offs": trade_offs,
        "errors": errors,
        "tested_values": len(frame),
        "conclusion": build_conclusion(
            adaptive_wins=adaptive_wins,
            static_wins=static_wins,
            ties=ties,
            trade_offs=trade_offs,
        ),
    }


def save_recall_plot(frame: pd.DataFrame, experiment_name: str) -> None:
    valid = frame.loc[frame["status"].eq("success")].copy()
    if valid.empty:
        return

    figure, axis = plt.subplots(figsize=(9, 5))

    axis.plot(
        valid["parameter_value"],
        valid["static_recall"],
        marker="o",
        label="Static",
    )
    axis.plot(
        valid["parameter_value"],
        valid["adaptive_recall"],
        marker="o",
        label="Adaptive",
    )

    axis.set_title(f"Recall sensitivity: {experiment_name}")
    axis.set_xlabel(frame["api_parameter"].iloc[0])
    axis.set_ylabel("Recall")
    axis.legend()
    axis.grid(True, alpha=0.3)

    figure.tight_layout()
    figure.savefig(
        OUTPUT_DIR / experiment_name / "recall_comparison.png",
        dpi=160,
        bbox_inches="tight",
    )
    plt.close(figure)


def save_cost_plot(frame: pd.DataFrame, experiment_name: str) -> None:
    valid = frame.loc[frame["status"].eq("success")].copy()
    if valid.empty:
        return

    figure, axis = plt.subplots(figsize=(9, 5))

    axis.plot(
        valid["parameter_value"],
        valid["static_operational_cost"],
        marker="o",
        label="Static",
    )
    axis.plot(
        valid["parameter_value"],
        valid["adaptive_operational_cost"],
        marker="o",
        label="Adaptive",
    )

    axis.set_title(f"Operational-cost sensitivity: {experiment_name}")
    axis.set_xlabel(frame["api_parameter"].iloc[0])
    axis.set_ylabel("Total operational cost")
    axis.legend()
    axis.grid(True, alpha=0.3)

    figure.tight_layout()
    figure.savefig(
        OUTPUT_DIR / experiment_name / "operational_cost_comparison.png",
        dpi=160,
        bbox_inches="tight",
    )
    plt.close(figure)


def save_difference_plot(frame: pd.DataFrame, experiment_name: str) -> None:
    valid = frame.loc[frame["status"].eq("success")].copy()
    if valid.empty:
        return

    figure, axis = plt.subplots(figsize=(9, 5))

    axis.axhline(0.0, linewidth=1)
    axis.plot(
        valid["parameter_value"],
        valid["recall_difference"],
        marker="o",
    )

    axis.set_title(f"Adaptive recall difference: {experiment_name}")
    axis.set_xlabel(frame["api_parameter"].iloc[0])
    axis.set_ylabel("Adaptive recall - Static recall")
    axis.grid(True, alpha=0.3)

    figure.tight_layout()
    figure.savefig(
        OUTPUT_DIR / experiment_name / "recall_difference.png",
        dpi=160,
        bbox_inches="tight",
    )
    plt.close(figure)


def save_summary_plot(summary_frame: pd.DataFrame) -> None:
    if summary_frame.empty:
        return

    plot_frame = summary_frame.set_index("parameter_tested")[
        ["adaptive_wins", "static_wins", "ties", "trade_offs"]
    ]

    axis = plot_frame.plot(
        kind="bar",
        figsize=(11, 6),
    )
    axis.set_title("Robustness analysis: policy outcomes by tested parameter")
    axis.set_xlabel("Parameter tested")
    axis.set_ylabel("Number of tested settings")
    axis.tick_params(axis="x", rotation=30)
    axis.legend(
        [
            "Adaptive wins",
            "Static wins",
            "Ties",
            "Trade-offs",
        ]
    )
    axis.grid(True, axis="y", alpha=0.3)

    figure = axis.get_figure()
    figure.tight_layout()
    figure.savefig(
        OUTPUT_DIR / "robustness_summary.png",
        dpi=160,
        bbox_inches="tight",
    )
    plt.close(figure)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Run one-factor-at-a-time robustness experiments for "
            "Static and Adaptive sequential fraud policies."
        )
    )
    parser.add_argument(
        "--api-base-url",
        default=API_BASE_URL,
        help=f"FastAPI base URL. Default: {API_BASE_URL}",
    )
    parser.add_argument(
        "--timeout",
        type=int,
        default=300,
        help="Timeout in seconds for each API request.",
    )
    parser.add_argument(
        "--pause",
        type=float,
        default=0.0,
        help="Optional pause in seconds between API requests.",
    )
    parser.add_argument(
        "--experiment",
        choices=["all", *EXPERIMENTS.keys()],
        default="all",
        help="Run all experiments or only one named experiment.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    if args.experiment == "all":
        selected_experiments = EXPERIMENTS
    else:
        selected_experiments = {
            args.experiment: EXPERIMENTS[args.experiment]
        }

    detailed_frames: list[pd.DataFrame] = []
    summary_rows: list[dict[str, Any]] = []

    with requests.Session() as session:
        for experiment_name, configuration in selected_experiments.items():
            experiment_dir = OUTPUT_DIR / experiment_name
            experiment_dir.mkdir(parents=True, exist_ok=True)

            frame = run_experiment(
                session=session,
                experiment_name=experiment_name,
                api_parameter=configuration["api_parameter"],
                values=configuration["values"],
                base_params=BASE_PARAMS,
                api_base_url=args.api_base_url,
                timeout=args.timeout,
                pause_seconds=args.pause,
            )

            frame.to_csv(
                experiment_dir / "results.csv",
                index=False,
            )

            save_recall_plot(frame, experiment_name)
            save_cost_plot(frame, experiment_name)
            save_difference_plot(frame, experiment_name)

            detailed_frames.append(frame)
            summary_rows.append(summarise_experiment(frame))

    all_results = pd.concat(
        detailed_frames,
        ignore_index=True,
        sort=False,
    )
    all_results.to_csv(
        OUTPUT_DIR / "robustness_detailed_results.csv",
        index=False,
    )

    summary_frame = pd.DataFrame(summary_rows)
    summary_frame.to_csv(
        OUTPUT_DIR / "robustness_summary.csv",
        index=False,
    )

    save_summary_plot(summary_frame)

    print("\n")
    print("=" * 88)
    print("ROBUSTNESS ANALYSIS SUMMARY")
    print("=" * 88)

    printable = summary_frame.rename(
        columns={
            "parameter_tested": "Parameter tested",
            "adaptive_wins": "Adaptive wins",
            "static_wins": "Static wins",
            "ties": "Ties",
            "trade_offs": "Trade-offs",
            "errors": "Errors",
            "tested_values": "Tested values",
            "conclusion": "Conclusion",
        }
    )

    print(printable.to_string(index=False))

    print("\nFiles created:")
    print(f"  {OUTPUT_DIR / 'robustness_summary.csv'}")
    print(f"  {OUTPUT_DIR / 'robustness_detailed_results.csv'}")
    print(f"  {OUTPUT_DIR / 'robustness_summary.png'}")

    for experiment_name in selected_experiments:
        print(f"  {OUTPUT_DIR / experiment_name / 'results.csv'}")
        print(f"  {OUTPUT_DIR / experiment_name / 'recall_comparison.png'}")
        print(
            f"  {OUTPUT_DIR / experiment_name / 'operational_cost_comparison.png'}"
        )
        print(f"  {OUTPUT_DIR / experiment_name / 'recall_difference.png'}")


if __name__ == "__main__":
    main()
