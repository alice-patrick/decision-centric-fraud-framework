from pathlib import Path
import joblib


def load_model(model_path: str):
    path = Path(model_path)

    if not path.exists():
        raise FileNotFoundError(f"Model artifact not found: {model_path}")

    model = joblib.load(path)
    return model


def save_model(model, model_path: str) -> None:
    path = Path(model_path)
    path.parent.mkdir(parents=True, exist_ok=True)

    joblib.dump(model, path)