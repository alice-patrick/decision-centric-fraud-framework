def apply_static_threshold(score: float, threshold: float) -> bool:
    return score >= threshold


def get_adaptive_threshold(
    base_threshold: float,
    current_alert_rate: float,
    alert_rate_low: float,
    alert_rate_high: float,
    min_threshold: float = 0.05,
    max_threshold: float = 0.95,
    adjustment: float = 0.10
) -> float:

    if current_alert_rate > alert_rate_high:
        return min(base_threshold + adjustment, max_threshold)

    if current_alert_rate < alert_rate_low:
        return max(base_threshold - adjustment, min_threshold)

    return base_threshold


def apply_adaptive_threshold(
    score: float,
    base_threshold: float,
    current_alert_rate: float,
    alert_rate_low: float,
    alert_rate_high: float
):
    threshold_used = get_adaptive_threshold(
        base_threshold=base_threshold,
        current_alert_rate=current_alert_rate,
        alert_rate_low=alert_rate_low,
        alert_rate_high=alert_rate_high
    )

    decision = score >= threshold_used

    return decision, threshold_used