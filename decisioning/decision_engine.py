from decisioning.thresholding import apply_static_threshold, apply_adaptive_threshold
from decisioning.cost_logic import apply_cost_aware_decision


def assign_alert_severity(
    fraud_score: float,
    expected_fraud_loss: float,
) -> str:
    if fraud_score >= 0.90 and expected_fraud_loss >= 100000:
        return "HIGH"

    if fraud_score >= 0.75 and expected_fraud_loss >= 25000:
        return "MEDIUM"

    return "LOW"


def make_decision(
    score: float,
    amount: float,
    config: dict,
    mode: str = "static",
    current_alert_rate: float | None = None,
) -> dict:
    decision_cfg = config["decisioning"]

    if mode == "static":
        base_decision = apply_static_threshold(
            score=score,
            threshold=decision_cfg["static_threshold"],
        )
        threshold_used = decision_cfg["static_threshold"]

    elif mode == "adaptive":
        if current_alert_rate is None:
            raise ValueError("current_alert_rate is required for adaptive mode.")

        base_decision, threshold_used = apply_adaptive_threshold(
            score=score,
            base_threshold=decision_cfg["static_threshold"],
            current_alert_rate=current_alert_rate,
            alert_rate_low=decision_cfg["alert_rate_low"],
            alert_rate_high=decision_cfg["alert_rate_high"],
        )

    else:
        raise ValueError(f"Unsupported decision mode: {mode}")

    final_decision, cost_details = apply_cost_aware_decision(
        score=score,
        amount=amount,
        base_decision=base_decision,
        false_positive_cost=decision_cfg["cost_false_positive"],
        false_negative_factor=decision_cfg["cost_false_negative_factor"],
    )

    severity = (
        assign_alert_severity(
            fraud_score=score,
            expected_fraud_loss=cost_details["expected_fraud_loss"],
        )
        if final_decision
        else "NONE"
    )

    reason = build_decision_reason(
        base_decision=base_decision,
        cost_decision=cost_details["cost_decision"],
        final_decision=final_decision,
        mode=mode,
        severity=severity,
    )

    return {
        "score": score,
        "amount": amount,
        "mode": mode,
        "threshold_used": threshold_used,
        "base_decision": base_decision,
        "cost_decision": cost_details["cost_decision"],
        "final_decision": final_decision,
        "decision": "alert" if final_decision else "no_alert",
        "severity": severity,
        "reason": reason,
        "expected_fraud_loss": cost_details["expected_fraud_loss"],
        "expected_investigation_cost": cost_details["expected_investigation_cost"],
    }


def build_decision_reason(
    base_decision: bool,
    cost_decision: bool,
    final_decision: bool,
    mode: str,
    severity: str,
) -> str:
    if not final_decision:
        return "score_below_threshold_and_cost_not_justified"

    if severity == "HIGH":
        return "very_high_risk_and_high_expected_loss"

    if severity == "MEDIUM":
        return "elevated_risk_and_material_expected_loss"

    if severity == "LOW":
        return "selected_by_decision_policy_low_priority"

    if base_decision and cost_decision:
        return f"{mode}_threshold_exceeded_and_cost_justified"

    if base_decision:
        return f"{mode}_threshold_exceeded"

    if cost_decision:
        return "cost_justified_alert"

    return "unknown"