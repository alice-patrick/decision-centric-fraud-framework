import pandas as pd
import pytest

from app.services.analyst_queue_service import (
    build_analyst_queue,
    get_selected_alerts,
)


def sample_alerts():
    return pd.DataFrame(
        {
            "transaction_id": [1, 2, 3, 4, 5],
            "alert": [1, 1, 1, 1, 0],
            "rank_score": [100.0, 90.0, 80.0, 70.0, 200.0],
            "analyst_priority": [2, 1, 1, 3, 1],
        }
    )


def test_analyst_capacity_is_respected():
    df = sample_alerts()

    result = build_analyst_queue(
        df=df,
        analyst_capacity=2,
    )

    assert "selected_for_review" in result.columns

    selected_count = int(
        result["selected_for_review"].sum()
    )

    assert selected_count <= 2


def test_only_alerts_can_be_selected_for_review():
    df = sample_alerts()

    result = build_analyst_queue(
        df=df,
        analyst_capacity=10,
    )

    selected = result[
        result["selected_for_review"] == 1
    ]

    assert (selected["alert"] == 1).all()


def test_queue_prioritises_analyst_priority_then_rank_score():
    df = sample_alerts()

    result = build_analyst_queue(
        df=df,
        analyst_capacity=3,
    )

    selected = get_selected_alerts(
        df=result,
    )

    assert selected["transaction_id"].tolist() == [
        2,
        3,
        1,
    ]


def test_queue_positions_are_sequential():
    df = sample_alerts()

    result = build_analyst_queue(
        df=df,
        analyst_capacity=3,
    )

    selected = get_selected_alerts(
        df=result,
    )

    assert selected["queue_position"].tolist() == [
        1,
        2,
        3,
    ]


def test_zero_capacity_selects_no_alerts():
    df = sample_alerts()

    result = build_analyst_queue(
        df=df,
        analyst_capacity=0,
    )

    assert int(
        result["selected_for_review"].sum()
    ) == 0


def test_negative_capacity_raises_value_error():
    df = sample_alerts()

    with pytest.raises(ValueError):
        build_analyst_queue(
            df=df,
            analyst_capacity=-1,
        )


def test_missing_required_column_raises_value_error():
    df = sample_alerts().drop(
        columns=["rank_score"]
    )

    with pytest.raises(ValueError):
        build_analyst_queue(
            df=df,
            analyst_capacity=2,
        )


def test_get_selected_alerts_respects_limit():
    df = sample_alerts()

    queue_df = build_analyst_queue(
        df=df,
        analyst_capacity=4,
    )

    selected = get_selected_alerts(
        df=queue_df,
        limit=2,
    )

    assert len(selected) == 2


def test_get_selected_alerts_requires_queue_columns():
    df = sample_alerts()

    with pytest.raises(ValueError):
        get_selected_alerts(
            df=df,
        )


def test_negative_limit_raises_value_error():
    df = sample_alerts()

    queue_df = build_analyst_queue(
        df=df,
        analyst_capacity=4,
    )

    with pytest.raises(ValueError):
        get_selected_alerts(
            df=queue_df,
            limit=-1,
        )