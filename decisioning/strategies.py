from __future__ import annotations

from dataclasses import dataclass

import pandas as pd

from decisioning.ranking import (
    calculate_expected_fraud_loss,
    calculate_expected_investigation_cost,
    calculate_rank_score,
)


@dataclass
class BaseDecisionStrategy:
    decision_col: str = "decision"
    strategy_name: str = "base"

    def select(self, df: pd.DataFrame) -> pd.DataFrame:
        raise NotImplementedError("Each strategy must implement select().")

    def _validate_columns(
        self,
        df: pd.DataFrame,
        required_cols: list[str],
    ) -> None:
        missing = [col for col in required_cols if col not in df.columns]

        if missing:
            raise ValueError(f"Missing required columns: {missing}")

    def _reset_decision_column(
        self,
        df: pd.DataFrame,
    ) -> pd.DataFrame:
        df = df.copy()
        df[self.decision_col] = 0
        df["strategy"] = self.strategy_name

        return df


@dataclass
class StaticThresholdStrategy(BaseDecisionStrategy):
    threshold: float = 0.5
    score_col: str = "fraud_score"
    strategy_name: str = "static_threshold"

    def select(self, df: pd.DataFrame) -> pd.DataFrame:
        self._validate_columns(df, [self.score_col])

        df = self._reset_decision_column(df)

        df[self.decision_col] = (
            df[self.score_col] >= self.threshold
        ).astype(int)

        df["rank_score"] = df[self.score_col]
        df["threshold_used"] = self.threshold

        return df


@dataclass
class TopKStrategy(BaseDecisionStrategy):
    k: int = 100
    score_col: str = "fraud_score"
    strategy_name: str = "top_k"

    def select(self, df: pd.DataFrame) -> pd.DataFrame:
        self._validate_columns(df, [self.score_col])

        if self.k <= 0:
            raise ValueError("k must be greater than 0.")

        df = self._reset_decision_column(df)

        selected_indices = (
            df.sort_values(
                self.score_col,
                ascending=False,
            )
            .head(self.k)
            .index
        )

        df.loc[selected_indices, self.decision_col] = 1
        df["rank_score"] = df[self.score_col]

        return df


@dataclass
class StaticThresholdCappedStrategy(BaseDecisionStrategy):
    threshold: float = 0.5
    k: int = 100
    score_col: str = "fraud_score"
    strategy_name: str = "static_threshold_capped"

    def select(self, df: pd.DataFrame) -> pd.DataFrame:
        self._validate_columns(df, [self.score_col])

        if self.k <= 0:
            raise ValueError("k must be greater than 0.")

        df = self._reset_decision_column(df)

        candidates = df[
            df[self.score_col] >= self.threshold
        ]

        selected_indices = (
            candidates.sort_values(
                self.score_col,
                ascending=False,
            )
            .head(self.k)
            .index
        )

        df.loc[selected_indices, self.decision_col] = 1
        df["rank_score"] = df[self.score_col]
        df["threshold_used"] = self.threshold

        return df


@dataclass
class CostAwareStrategy(BaseDecisionStrategy):
    k: int = 100
    score_col: str = "fraud_score"
    amount_col: str = "amount"
    false_positive_cost: float = 50.0
    false_negative_factor: float = 1.0
    strategy_name: str = "cost_aware_ranking"

    def select(self, df: pd.DataFrame) -> pd.DataFrame:
        self._validate_columns(
            df,
            [self.score_col, self.amount_col],
        )

        if self.k <= 0:
            raise ValueError("k must be greater than 0.")

        df = self._reset_decision_column(df)

        df["expected_fraud_loss"] = (
            calculate_expected_fraud_loss(
                fraud_score=df[self.score_col],
                amount=df[self.amount_col],
                false_negative_factor=self.false_negative_factor,
            )
        )

        df["expected_investigation_cost"] = (
            calculate_expected_investigation_cost(
                fraud_score=df[self.score_col],
                investigation_cost=self.false_positive_cost,
            )
        )

        df["rank_score"] = calculate_rank_score(
            fraud_score=df[self.score_col],
            amount=df[self.amount_col],
            investigation_cost=self.false_positive_cost,
            false_negative_factor=self.false_negative_factor,
        )

        selected_indices = (
            df.sort_values(
                "rank_score",
                ascending=False,
            )
            .head(self.k)
            .index
        )

        df.loc[selected_indices, self.decision_col] = 1

        return df


@dataclass
class FullDecisionSystemStrategy(BaseDecisionStrategy):
    k: int = 100
    score_col: str = "fraud_score"
    amount_col: str = "amount"
    entity_col: str = "entity_id"
    false_positive_cost: float = 50.0
    false_negative_factor: float = 1.0
    strategy_name: str = "full_decision_system"

    def select(self, df: pd.DataFrame) -> pd.DataFrame:
        self._validate_columns(
            df,
            [
                self.score_col,
                self.amount_col,
                self.entity_col,
            ],
        )

        if self.k <= 0:
            raise ValueError("k must be greater than 0.")

        df = self._reset_decision_column(df)

        df["expected_fraud_loss"] = (
            calculate_expected_fraud_loss(
                fraud_score=df[self.score_col],
                amount=df[self.amount_col],
                false_negative_factor=self.false_negative_factor,
            )
        )

        df["expected_investigation_cost"] = (
            calculate_expected_investigation_cost(
                fraud_score=df[self.score_col],
                investigation_cost=self.false_positive_cost,
            )
        )

        df["rank_score"] = calculate_rank_score(
            fraud_score=df[self.score_col],
            amount=df[self.amount_col],
            investigation_cost=self.false_positive_cost,
            false_negative_factor=self.false_negative_factor,
        )

        df["suppressed"] = 0

        ranked_indices = (
            df.sort_values(
                "rank_score",
                ascending=False,
            )
            .index
        )

        selected_entities = set()
        selected_count = 0

        for idx in ranked_indices:
            if selected_count >= self.k:
                break

            entity_id = df.at[idx, self.entity_col]

            if entity_id in selected_entities:
                df.at[idx, "suppressed"] = 1
                continue

            df.at[idx, self.decision_col] = 1
            selected_entities.add(entity_id)
            selected_count += 1

        return df