import json
from datetime import datetime, timezone

from app.core.paths import LOGS_DIR


def write_json_log(log_filename: str, payload: dict) -> None:
    LOGS_DIR.mkdir(parents=True, exist_ok=True)

    log_path = LOGS_DIR / log_filename

    record = {
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        **payload,
    }

    with open(log_path, "a", encoding="utf-8") as file:
        file.write(json.dumps(record) + "\n")