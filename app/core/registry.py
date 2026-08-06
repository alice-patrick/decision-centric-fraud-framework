from app.core.paths import MODELS_DIR
import json


def load_model_registry(registry_filename: str) -> dict:
    path = MODELS_DIR / registry_filename

    if not path.exists():
        raise FileNotFoundError(f"Model registry not found: {path}")

    with open(path, "r", encoding="utf-8") as file:
        registry = json.load(file)

    if "active_model" not in registry:
        raise KeyError("Registry must contain an 'active_model' field.")

    if "models" not in registry:
        raise KeyError("Registry must contain a 'models' field.")

    return registry


def get_active_model_info(registry: dict) -> dict:
    active_model = registry["active_model"]

    if active_model not in registry["models"]:
        raise KeyError(f"Active model '{active_model}' not found in registry.")

    return registry["models"][active_model]