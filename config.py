from pathlib import Path
import os
from dotenv import load_dotenv
ROOT: Path = Path(__file__).resolve().parent
load_dotenv(ROOT / ".env")
DOCUMENTS: Path = ROOT / "data" / "documents"
WORKSPACE: Path = ROOT / "workspace"
LOGS: Path = ROOT / "logs"
for folder in (DOCUMENTS, WORKSPACE, LOGS):
    folder.mkdir(parents=True, exist_ok=True)
DB_PATH: Path = ROOT / "agent.sqlite3"
BASE_URL: str = os.getenv("LM_STUDIO_BASE_URL", "http://127.0.0.1:1234/v1").rstrip("/")
MODEL_ID: str = os.getenv("LM_STUDIO_MODEL", "").strip()
API_KEY: str = os.getenv("LM_STUDIO_API_KEY", "lm-studio")
MAX_STEPS: int = max(1, min(10, int(os.getenv("AGENT_MAX_STEPS", "5"))))
TIMEOUT: int = max(10, int(os.getenv("AGENT_TIMEOUT_SECONDS", "180")))
