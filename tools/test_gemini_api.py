"""Test Gemini API key/model catalog without starting Gradio. Never prints the key."""
# loads .env from this project directory
import sys
from pathlib import Path

# プロジェクトのルートディレクトリをPythonの検索パスに追加
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from config import ROOT  # noqa: E402
from src.providers import list_provider_models

if __name__ == "__main__":
    try:
        models = list_provider_models("gemini")
    except Exception as exc:
        print(f"FAILED: {type(exc).__name__}: {exc}")
        raise SystemExit(1)
    print(f"OK: {len(models)} Gemini generateContent model(s) returned")
    for model in models:
        print(model)
