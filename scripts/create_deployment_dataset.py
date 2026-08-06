from pathlib import Path

import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[1]

SOURCE_PATH = (
    PROJECT_ROOT
    / "data"
    / "raw"
    / "AIML Dataset.csv"
)

TARGET_PATH = (
    PROJECT_ROOT
    / "data"
    / "deployment"
    / "paysim_deployment_sample.csv"
)

ROW_LIMIT = 50_000


def main() -> None:
    if not SOURCE_PATH.exists():
        raise FileNotFoundError(
            f"Source dataset not found: {SOURCE_PATH}"
        )

    TARGET_PATH.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    df = pd.read_csv(
        SOURCE_PATH,
        nrows=ROW_LIMIT,
    )

    if "step" not in df.columns:
        raise ValueError(
            "The dataset does not contain the 'step' column."
        )

    df = df.sort_values("step").reset_index(drop=True)

    df.to_csv(
        TARGET_PATH,
        index=False,
    )

    print(
        f"Saved {len(df):,} rows to: "
        f"{TARGET_PATH}"
    )


if __name__ == "__main__":
    main()