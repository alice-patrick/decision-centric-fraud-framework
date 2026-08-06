from pathlib import Path

import pandas as pd


DATASET_COLUMNS = [
    "step",
    "type",
    "amount",
    "oldbalanceOrg",
    "newbalanceOrig",
    "oldbalanceDest",
    "newbalanceDest",
    "isFraud",
]


def load_data(
    project_root: Path,
    limit: int = 10000,
) -> pd.DataFrame:
    """
    Load and validate PaySim transactions.
    """
    if limit <= 0:
        raise ValueError(
            "limit must be greater than 0."
        )

    dataset_path = (
        project_root
        / "data"
        / "raw"
        / "AIML Dataset.csv"
    )

    if not dataset_path.exists():
        raise FileNotFoundError(
            f"Dataset not found: {dataset_path}"
        )

    df = pd.read_csv(dataset_path).head(limit)

    missing_columns = [
        column
        for column in DATASET_COLUMNS
        if column not in df.columns
    ]

    if missing_columns:
        raise ValueError(
            f"Missing required columns: {missing_columns}"
        )

    df = df[DATASET_COLUMNS].copy()
    df = df.sort_values("step").reset_index(drop=True)

    df["transaction_id"] = df.index

    # Simulation proxy only.
    # This is not a real customer or account identifier.
    df["simulation_entity_key"] = (
        df["type"].astype(str)
        + "_"
        + df["amount"]
        .round(-2)
        .astype(int)
        .astype(str)
    )

    return df