from pathlib import Path
import yaml
from app.core.paths import CONFIG_DIR


def load_config(config_name: str = "config.yaml") -> dict:
    path = CONFIG_DIR / config_name

    if not path.exists():
        raise FileNotFoundError(f"Config file not found: {path}")

    with open(path, "r", encoding="utf-8") as file:
        config = yaml.safe_load(file)

    if config is None:
        raise ValueError("Config file is empty.")

    return config