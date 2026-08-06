from __future__ import annotations

import os
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


def resolve_dataset_path(project_root: Path) -> Path:
    """
    Resolve the dataset path for local and cloud execution.

    Priority:
    1. DATASET_PATH environment variable, when explicitly provided.
    2. Full local PaySim dataset.
    3. Smaller deployment dataset used by Render.
    """
    configured_path = os.getenv("DATASET_PATH")

    if configured_path:
        dataset_path = Path(configured_path)

        if not dataset_path.is_absolute():
            dataset_path = project_root / dataset_path

        return dataset_path

    local_dataset_path = (
        project_root
        / "data"
        / "raw"
        / "AIML Dataset.csv"
    )

    deployment_dataset_path = (
        project_root
        / "data"
        / "deployment"
        / "paysim_deployment_sample.csv"
    )

    if local_dataset_path.exists():
        return local_dataset_path

    return deployment_dataset_path


def load_data(
    project_root: Path,
    limit: int = 10000,
) -> pd.DataFrame:
    """
    Load and validate PaySim transactions.

    Locally, the full PaySim dataset is used when available.
    In cloud deployment, the smaller deployment sample is used.
    """
    if limit <= 0:
        raise ValueError(
            "limit must be greater than 0."
        )

    dataset_path = resolve_dataset_path(project_root)

    if not dataset_path.exists():
        raise FileNotFoundError(
            "Dataset not found. Checked path: "
            f"{dataset_path}. "
            "Provide DATASET_PATH or add the deployment dataset."
        )

    # Read only the rows required by the selected experiment.
    # This avoids loading the full six-million-row dataset into memory.
    df = pd.read_csv(
        dataset_path,
        nrows=limit,
        usecols=lambda column: column in DATASET_COLUMNS,
    )

    missing_columns = [
        column
        for column in DATASET_COLUMNS
        if column not in df.columns
    ]

    if missing_columns:
        raise ValueError(
            f"Missing required columns: {missing_columns}"
        )

    if len(df) < limit:
        raise ValueError(
            f"The dataset contains only {len(df):,} rows, "
            f"but the requested limit is {limit:,}."
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