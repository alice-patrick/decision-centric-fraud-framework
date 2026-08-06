import pandas as pd

from decisioning.analyst_budget import apply_analyst_budget


def validate_analyst_capacity(
    analyst_capacity: int,
) -> None:
    """
    Validate the maximum number of alerts
    that analysts can review.
    """
    if analyst_capacity < 0:
        raise ValueError(
            "analyst_capacity must be non-negative."
        )


def add_queue_position(
    df: pd.DataFrame,
) -> pd.DataFrame:
    """
    Add a one-based queue position to every alert
    selected for analyst review.
    """
    result_df = df.copy()
    result_df["queue_position"] = pd.Series(
        pd.NA,
        index=result_df.index,
        dtype="Int64",
    )

    selected_mask = (
        result_df["selected_for_review"] == 1
    )

    selected_indices = (
        result_df.loc[selected_mask]
        .sort_values(
            [
                "analyst_priority",
                "rank_score",
            ],
            ascending=[
                True,
                False,
            ],
        )
        .index
    )

    result_df.loc[
        selected_indices,
        "queue_position",
    ] = range(
        1,
        len(selected_indices) + 1,
    )

    return result_df


def build_analyst_queue(
    df: pd.DataFrame,
    analyst_capacity: int,
) -> pd.DataFrame:
    """
    Apply analyst capacity and organise the generated
    alerts into a prioritised analyst queue.
    """
    validate_analyst_capacity(
        analyst_capacity=analyst_capacity
    )

    required_columns = {
        "alert",
        "rank_score",
        "analyst_priority",
    }

    missing_columns = required_columns.difference(
        df.columns
    )

    if missing_columns:
        raise ValueError(
            "Missing required analyst queue columns: "
            f"{sorted(missing_columns)}"
        )

    queue_df = apply_analyst_budget(
        df=df,
        analyst_capacity=analyst_capacity,
    )

    queue_df = add_queue_position(
        df=queue_df
    )

    queue_df = queue_df.sort_values(
        [
            "selected_for_review",
            "analyst_priority",
            "rank_score",
        ],
        ascending=[
            False,
            True,
            False,
        ],
    )

    return queue_df


def get_selected_alerts(
    df: pd.DataFrame,
    limit: int | None = None,
) -> pd.DataFrame:
    """
    Return only alerts selected for analyst review,
    ordered by their queue position.
    """
    if "selected_for_review" not in df.columns:
        raise ValueError(
            "selected_for_review column is missing. "
            "Run build_analyst_queue first."
        )

    if "queue_position" not in df.columns:
        raise ValueError(
            "queue_position column is missing. "
            "Run build_analyst_queue first."
        )

    if limit is not None and limit < 0:
        raise ValueError(
            "limit must be non-negative."
        )

    selected_df = df[
        df["selected_for_review"] == 1
    ].copy()

    selected_df = selected_df.sort_values(
        "queue_position",
        ascending=True,
    )

    if limit is not None:
        selected_df = selected_df.head(limit)

    return selected_df