def calculate_expected_fraud_loss(
    score: float,
    amount: float,
    false_negative_factor: float = 1.0
) -> float:
    return score * amount * false_negative_factor


def calculate_expected_investigation_cost(
    score: float,
    false_positive_cost: float = 1.0
) -> float:
    return (1 - score) * false_positive_cost


def apply_cost_aware_decision(
    score: float,
    amount: float,
    base_decision: bool,
    false_positive_cost: float,
    false_negative_factor: float
):
    expected_fraud_loss = calculate_expected_fraud_loss(
        score=score,
        amount=amount,
        false_negative_factor=false_negative_factor
    )

    expected_investigation_cost = calculate_expected_investigation_cost(
        score=score,
        false_positive_cost=false_positive_cost
    )

    cost_decision = expected_fraud_loss > expected_investigation_cost
    final_decision = base_decision or cost_decision

    details = {
        "expected_fraud_loss": expected_fraud_loss,
        "expected_investigation_cost": expected_investigation_cost,
        "cost_decision": cost_decision
    }

    return final_decision, details