
"""Select an inference provider for both the Gradio UI and background worker.

Only the provider name and model ID are stored. API credentials remain in .env.
An empty preference database defaults to the existing local LM Studio backend.
"""

import os
import re
import sqlite3
import json
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from openai import OpenAI

from config import ROOT, TIMEOUT
from src import lmstudio

PREF_DB = ROOT / "provider_selection.sqlite3"

PROVIDERS = ("local", "openai", "gemini")

GEMINI_URL = (
    "https://generativelanguage.googleapis.com/v1beta/openai/"
)
GEMINI_MODELS_URL = (
    "https://generativelanguage.googleapis.com/v1beta/models"
)

MODEL_PATTERN = re.compile(
    r"^[A-Za-z0-9][A-Za-z0-9._:/+-]{0,127}$"
)


def _connect():
    """Open the settings database and ensure its table exists."""
    connection = sqlite3.connect(PREF_DB, timeout=20)
    connection.execute("PRAGMA busy_timeout=20000")
    connection.execute(
        "CREATE TABLE IF NOT EXISTS settings "
        "(name TEXT PRIMARY KEY, value TEXT NOT NULL)"
    )
    return connection


def _read_setting(key, default=""):
    """Read a persisted setting."""
    with _connect() as db:
        row = db.execute(
            "SELECT value FROM settings WHERE name=?",
            (key,),
        ).fetchone()

    return row[0] if row else default


def current_provider():
    """Return the selected provider, defaulting to LM Studio."""
    provider = _read_setting("provider", "local")
    return provider if provider in PROVIDERS else "local"


def current_selection():
    """Return the current provider and selected model."""
    provider = current_provider()

    if provider == "local":
        # Show the saved model preference without calling the local API.
        return provider, lmstudio._saved_model() or ""

    return provider, _read_setting(f"model_{provider}")


def configured(provider):
    """Check whether the selected provider has a usable API key."""
    if provider == "local":
        return True

    env_name = {
        "openai": "OPENAI_API_KEY",
        "gemini": "GEMINI_API_KEY",
    }.get(provider)

    if not env_name:
        raise ValueError("Unsupported provider")

    key = os.getenv(env_name, "").strip()

    return bool(
        key
        and not key.startswith("YOUR_")
        and key not in ("xxx", "your-key-here")
    )


def client_for(provider):
    """Create the inference client for the requested provider."""
    if provider == "local":
        return lmstudio.client()

    if provider not in ("openai", "gemini"):
        raise ValueError("Unsupported provider")

    if not configured(provider):
        name = (
            "OPENAI_API_KEY"
            if provider == "openai"
            else "GEMINI_API_KEY"
        )
        raise RuntimeError(
            f"{name} が設定されていません。.env を確認してください。"
        )

    if provider == "openai":
        return OpenAI(
            api_key=os.environ["OPENAI_API_KEY"].strip(),
            timeout=TIMEOUT,
            max_retries=0,
        )

    # Gemini OpenAI-compatible API client.
    # This client configuration alone does not guarantee that
    # thought_signature is preserved across tool-call turns.
    return OpenAI(
        api_key=os.environ["GEMINI_API_KEY"].strip(),
        base_url=GEMINI_URL,
        timeout=TIMEOUT,
        max_retries=0,
        default_headers={
            "x-goog-api-client": "lmstudio-multiprovider-agent/1.0"
        },
    )


def _google_error_message(raw_body):
    """Extract a useful message from Google's JSON error response."""
    try:
        payload = json.loads(
            raw_body.decode("utf-8", errors="replace")
        )
        error = (
            payload.get("error", {})
            if isinstance(payload, dict)
            else {}
        )

        message = (
            error.get("message")
            if isinstance(error, dict)
            else None
        )
        status = (
            error.get("status")
            if isinstance(error, dict)
            else None
        )

        parts = [str(value) for value in (status, message) if value]

        if parts:
            return ": ".join(parts)

        return raw_body.decode(
            "utf-8",
            errors="replace",
        )[:500]

    except (ValueError, TypeError):
        return raw_body.decode(
            "utf-8",
            errors="replace",
        )[:500]


def _list_gemini_models():
    """List Gemini models using Google's native Models API.

    The API key is sent in a request header rather than in the URL.
    """
    api_key = os.getenv("GEMINI_API_KEY", "").strip()

    if not api_key or not configured("gemini"):
        raise RuntimeError(
            "GEMINI_API_KEY が空かプレースホルダーです。"
            ".env と起動フォルダーを確認してください。"
        )

    found = []
    page_token = None
    seen_tokens = set()
    raw_count = 0

    while True:
        params = {"pageSize": 1000}

        if page_token:
            params["pageToken"] = page_token

        url = GEMINI_MODELS_URL + "?" + urlencode(params)

        request = Request(
            url,
            headers={
                "x-goog-api-key": api_key,
                "Accept": "application/json",
            },
            method="GET",
        )

        try:
            with urlopen(request, timeout=TIMEOUT) as response:
                status_code = getattr(response, "status", 200)
                raw = response.read()

        except HTTPError as exc:
            detail = _google_error_message(exc.read())
            raise RuntimeError(
                f"Gemini models.list HTTP {exc.code}: {detail}. "
                "Google AI Studioでキー、Gemini APIへのアクセス、"
                "APIキー制限、プロジェクト設定を確認してください。"
            ) from None

        except URLError as exc:
            reason = getattr(exc, "reason", exc)
            raise RuntimeError(
                f"Gemini APIへ接続できません: {reason}。"
                "ネットワーク、プロキシ、DNS、TLSを確認してください。"
            ) from None

        except TimeoutError:
            raise RuntimeError(
                "Gemini APIへの接続がタイムアウトしました。"
                "ネットワークを確認してください。"
            ) from None

        if status_code < 200 or status_code >= 300:
            raise RuntimeError(
                f"Gemini models.list HTTP {status_code}: "
                "応答を確認してください。"
            )

        try:
            payload = json.loads(raw.decode("utf-8"))

        except (UnicodeDecodeError, ValueError) as exc:
            raise RuntimeError(
                f"Gemini APIの応答をJSONとして解析できません: {exc}"
            ) from None

        if not isinstance(payload, dict):
            raise RuntimeError(
                "Gemini APIの応答形式が想定外です"
                "（JSONオブジェクトではありません）。"
            )

        page_models = payload.get("models", [])

        if not isinstance(page_models, list):
            raise RuntimeError(
                "Gemini APIの応答に models 配列がありません。"
            )

        raw_count += len(page_models)

        for item in page_models:
            if not isinstance(item, dict):
                continue

            actions = item.get("supportedGenerationMethods") or []

            if "generateContent" not in actions:
                continue

            # Prefer baseModelId; otherwise use models/<id>.
            model_id = item.get("baseModelId")

            if not model_id:
                model_id = str(
                    item.get("name", "")
                ).removeprefix("models/")

            if model_id.startswith("gemini-"):
                found.append(model_id)

        next_token = payload.get("nextPageToken")

        if not next_token:
            break

        if next_token in seen_tokens:
            raise RuntimeError(
                "Gemini APIが同じページトークンを繰り返しました。"
                "再試行してください。"
            )

        seen_tokens.add(next_token)
        page_token = next_token

    models = sorted(set(found))

    if not models:
        raise RuntimeError(
            "Google APIへの接続は成功しましたが、"
            "generateContent対応の gemini-* モデルが0件です "
            f"（API応答中のモデル数: {raw_count}）。"
            "キーが正しいプロジェクトのものか、Gemini APIの利用可否、"
            "モデル名と対応メソッドを確認してください。"
        )

    return models


def list_provider_models(provider):
    """Return model IDs available for the requested provider."""
    if provider not in PROVIDERS:
        raise ValueError("Unsupported provider")

    if provider == "local":
        return lmstudio.loaded_model_ids()

    if provider == "gemini":
        return _list_gemini_models()

    items = client_for(provider).models.list().data

    models = sorted({
        item.id
        for item in items
        if getattr(item, "id", None)
    })

    # Keep the existing OpenAI chat-model filter.
    # Gemini uses Google's native model catalog above.
    if provider == "openai":
        models = [
            item
            for item in models
            if item.startswith(
                ("gpt-", "o1", "o3", "o4", "o5", "o6")
            )
        ]

    return models


def set_provider(provider, model="", cloud_confirmed=False):
    """Persist provider/model selection after required cloud consent."""
    if provider not in PROVIDERS:
        raise ValueError("Unknown provider")

    if provider != "local":
        if not cloud_confirmed:
            raise ValueError(
                "オンラインAPIへの送信・課金について確認してください"
            )

        if not configured(provider):
            name = (
                "OPENAI_API_KEY"
                if provider == "openai"
                else "GEMINI_API_KEY"
            )
            raise RuntimeError(f"{name} が設定されていません")

        if (
            not isinstance(model, str)
            or not MODEL_PATTERN.fullmatch(model.strip())
        ):
            raise ValueError("有効なモデルIDを入力してください")

        model = model.strip()

    with _connect() as db:
        if provider != "local":
            db.execute(
                "INSERT INTO settings(name,value) VALUES(?,?) "
                "ON CONFLICT(name) DO UPDATE SET value=excluded.value",
                (f"model_{provider}", model),
            )

        db.execute(
            "INSERT INTO settings(name,value) VALUES('provider',?) "
            "ON CONFLICT(name) DO UPDATE SET value=excluded.value",
            (provider,),
        )

    suffix = f" ({model})" if provider != "local" else ""
    return f"推論先を {provider} に設定しました{suffix}"


def resolve_inference():
    """Resolve the active provider, model, and client."""
    provider = current_provider()

    if provider == "local":
        return (
            client_for(provider),
            lmstudio.selected_model(),
            provider,
        )

    model = _read_setting(f"model_{provider}")

    if not model:
        raise RuntimeError(
            "オンラインモデルが未選択です。"
            "Model Connectionで設定してください"
        )

    if not MODEL_PATTERN.fullmatch(model):
        raise RuntimeError("保存されたモデルIDが不正です")

    return client_for(provider), model, provider


def selection_status():
    """Return a UI-friendly summary of the current selection."""
    provider, model = current_selection()

    if provider == "local":
        return (
            "現在の推論先: LM Studio (local)\n"
            "選択済みインスタンス: "
            f"{model or '未選択（ロード済みモデルを自動検出）'}"
        )

    state = "設定済み" if configured(provider) else "未設定"

    return (
        f"現在の推論先: {provider}\n"
        f"モデルID: {model or '未選択'}\n"
        f"APIキー: {state}"
    )


# Jev settings are stored separately from cloud inference provider selection.

def jev_preferences():
    """Return (enabled, consented); Jev is opt-in and defaults off."""
    enabled = _read_setting("jev_enabled", "0") == "1"
    consented = _read_setting("jev_consent", "0") == "1"

    # Defense in depth: an enabled flag without consent is never honored.
    return enabled and consented, consented


def set_jev_preferences(enabled, consented):
    """Persist explicit Jev opt-in independently of OpenAI/Gemini consent."""
    enabled = bool(enabled)
    consented = bool(consented)

    if enabled and not consented:
        raise ValueError(
            "Jevを有効にするには、Jevへのデータ送信について同意が必要です"
        )

    with _connect() as db:
        db.execute(
            "INSERT INTO settings(name,value) VALUES('jev_enabled',?) "
            "ON CONFLICT(name) DO UPDATE SET value=excluded.value",
            ("1" if enabled else "0",),
        )

        db.execute(
            "INSERT INTO settings(name,value) VALUES('jev_consent',?) "
            "ON CONFLICT(name) DO UPDATE SET value=excluded.value",
            ("1" if consented else "0",),
        )

    return (
        "Jevの関連度判定を有効にしました"
        if enabled
        else "Jevの関連度判定を無効にしました"
    )

