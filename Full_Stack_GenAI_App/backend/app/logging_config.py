import json
import logging
from datetime import datetime, timezone
from pathlib import Path
from threading import Lock

class JsonLineLogger:
    """Thread-safe JSON Lines logger. Secrets must never be passed into fields."""
    def __init__(self, path: Path):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._lock = Lock()

    def write(self, **event):
        record = {"timestamp": datetime.now(timezone.utc).isoformat(), **event}
        with self._lock:
            with self.path.open("a", encoding="utf-8") as handle:
                handle.write(json.dumps(record, ensure_ascii=False, default=str) + "\n")

def get_loggers(log_dir: Path):
    log_dir.mkdir(parents=True, exist_ok=True)
    return (
        JsonLineLogger(log_dir / "requests.jsonl"),
        JsonLineLogger(log_dir / "tool_events.jsonl"),
    )
