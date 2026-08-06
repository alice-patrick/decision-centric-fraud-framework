import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from app.core.config_loader import load_config
from app.core.registry import load_model_registry, get_active_model_info
from app.model.save_load import load_model
from app.model.predict import predict_proba


def main():
    config = load_config()

    registry = load_model_registry(config["model"]["registry_path"])
    model_info = get_active_model_info(registry)

    model = load_model(model_info["path"])

    print("Config loaded successfully.")
    print(f"Active model: {registry['active_model']}")
    print(f"Model path: {model_info['path']}")
    print(f"Loaded model type: {type(model).__name__}")

    dummy_input = {
        "step": 1,
        "type": "PAYMENT",
        "amount": 1000,
        "oldbalanceOrg": 5000,
        "newbalanceOrig": 4000,
        "oldbalanceDest": 0,
        "newbalanceDest": 0
    }

    score = predict_proba(model, dummy_input)

    print("Fraud score:", score)


if __name__ == "__main__":
    main()