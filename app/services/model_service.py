import pandas as pd

from app.core.config_loader import load_config
from app.core.registry import (
    get_active_model_info,
    load_model_registry,
)
from app.model.save_load import load_model


MODEL_FEATURE_COLUMNS = [
    "step",
    "type",
    "amount",
    "oldbalanceOrg",
    "newbalanceOrig",
    "oldbalanceDest",
    "newbalanceDest",
]


def load_active_model():
    """
    Load the configuration and the active registered model.
    """
    config = load_config()

    registry = load_model_registry(
        config["model"]["registry_path"]
    )

    model_info = get_active_model_info(registry)
    model = load_model(model_info["path"])

    return config, model


def score_data(
    df: pd.DataFrame,
    model,
) -> pd.DataFrame:
    """
    Generate fraud probabilities for the transactions.
    """
    missing_columns = [
        column
        for column in MODEL_FEATURE_COLUMNS
        if column not in df.columns
    ]

    if missing_columns:
        raise ValueError(
            f"Missing model feature columns: {missing_columns}"
        )

    scored_df = df.copy()

    scored_df["fraud_score"] = model.predict_proba(
        scored_df[MODEL_FEATURE_COLUMNS]
    )[:, 1]

    return scored_df