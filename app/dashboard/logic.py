from __future__ import annotations

from typing import Any

import pandas as pd


def n(value: Any, default: float = 0.0) -> float:
    try:
        if value is None or pd.isna(value):
            return default
        return float(value)
    except (TypeError, ValueError):
        return default


def i(value: Any) -> int:
    return int(round(n(value)))


def optional_i(value: Any) -> int | None:
    if value is None:
        return None

    try:
        if pd.isna(value):
            return None
    except (TypeError, ValueError):
        pass

    try:
        return int(round(float(value)))
    except (TypeError, ValueError):
        return None


def get_summary(
    payload: dict[str, Any],
    key: str,
) -> dict[str, Any]:
    return payload.get(key, {}).get("summary", {})


def normalise_windows(
    frame: pd.DataFrame,
) -> pd.DataFrame:
    if frame.empty:
        return frame.copy()

    result = frame.copy().rename(
        columns={
            "monitoring_window": "window",
            "selected_alerts": "accepted_alerts",
            "suppressed_alerts": "suppressed",
            "capacity_rejected_alerts": "capacity_rejected",
            "policy_candidate_alerts": "candidate_alerts",
            "total_operational_cost": "operational_cost",
        }
    )

    if "window" in result.columns:
        result = result.sort_values("window")

    return result


def trend_label(series: pd.Series) -> str:
    clean = pd.to_numeric(
        series,
        errors="coerce",
    ).dropna()

    if len(clean) < 2:
        return "Insufficient data"

    first_value = float(clean.iloc[0])
    last_value = float(clean.iloc[-1])
    mean_value = float(clean.mean())
    value_range = float(
        clean.max() - clean.min()
    )

    if mean_value == 0:
        return (
            "Stable"
            if value_range == 0
            else "Variable"
        )

    relative_change = (
        last_value - first_value
    ) / abs(mean_value)

    relative_range = (
        value_range / abs(mean_value)
    )

    if relative_range < 0.15:
        return "Stable"

    if relative_change > 0.15:
        return "Generally increasing"

    if relative_change < -0.15:
        return "Generally decreasing"

    return "Variable"