import os
from pathlib import Path
from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parents[2]
load_dotenv(PROJECT_ROOT / ".env")

def _csv_env(name: str, default: str):
    return [item.strip() for item in os.getenv(name, default).split(",") if item.strip()]

API_KEYS = set(_csv_env("API_KEYS", "dev-local-key-change-me"))
RATE_LIMIT_REQUESTS = int(os.getenv("RATE_LIMIT_REQUESTS", "10"))
RATE_LIMIT_WINDOW_SECONDS = int(os.getenv("RATE_LIMIT_WINDOW_SECONDS", "60"))
MAX_AGENT_ITERATIONS = int(os.getenv("MAX_AGENT_ITERATIONS", "3"))
DEFAULT_TOP_K = int(os.getenv("DEFAULT_TOP_K", "3"))
KNOWLEDGE_BASE_PATH = PROJECT_ROOT / "backend" / "data" / "knowledge_base.md"
LOG_DIR = PROJECT_ROOT / "backend" / "logs"
