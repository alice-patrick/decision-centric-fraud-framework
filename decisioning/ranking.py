from __future__ import annotations

import pandas as pd


def calculate_expected_fraud_loss(
    fraud_score: pd.Series,
    amount: pd.Series,
    false_negative_factor: float = 1.0,
) -> pd.Series:
    """
    Calculate the expected financial loss if a transaction is not investigated.
    """
    return fraud_score * amount * false_negative_factor


def calculate_expected_investigation_cost(
    fraud_score: pd.Series,
    investigation_cost: float,
) -> pd.Series:
    """
    Calculate the expected cost associated with investigating a transaction.
    """
    return (1.0 - fraud_score) * investigation_cost


def calculate_expected_benefit(
    fraud_score: pd.Series,
    amount: pd.Series,
    investigation_cost: float,
    false_negative_factor: float = 1.0,
) -> pd.Series:
    """
    Calculate the expected operational benefit of investigating a transaction.
    """
    expected_fraud_loss = calculate_expected_fraud_loss(
        fraud_score=fraud_score,
        amount=amount,
        false_negative_factor=false_negative_factor,
    )

    expected_investigation_cost = calculate_expected_investigation_cost(
        fraud_score=fraud_score,
        investigation_cost=investigation_cost,
    )

    return expected_fraud_loss - expected_investigation_cost


def calculate_rank_score(
    fraud_score: pd.Series,
    amount: pd.Series,
    investigation_cost: float,
    false_negative_factor: float = 1.0,
) -> pd.Series:
    """
    Rank transactions according to their expected operational benefit.

    A higher score indicates that investigating the transaction is expected
    to provide greater operational value.
    """
    return calculate_expected_benefit(
        fraud_score=fraud_score,
        amount=amount,
        investigation_cost=investigation_cost,
        false_negative_factor=false_negative_factor,
    )