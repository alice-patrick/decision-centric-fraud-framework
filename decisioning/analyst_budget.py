import pandas as pd


def apply_analyst_budget(
    df: pd.DataFrame,
    analyst_capacity: int,
) -> pd.DataFrame:
    df = df.copy()

    df["selected_for_review"] = 0
    df["budget_overflow"] = 0

    alerts_df = df[df["alert"] == 1].copy()

    selected_indices = (
        alerts_df.sort_values(
            ["analyst_priority", "rank_score"],
            ascending=[True, False],
        )
        .head(analyst_capacity)
        .index
    )

    overflow_indices = alerts_df.index.difference(selected_indices)

    df.loc[selected_indices, "selected_for_review"] = 1
    df.loc[overflow_indices, "budget_overflow"] = 1

    return df