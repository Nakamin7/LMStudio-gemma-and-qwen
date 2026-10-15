from openai import OpenAI
from urllib.parse import urlsplit
import json
from urllib.request import Request, urlopen
from config import BASE_URL, API_KEY, MODEL_ID, TIMEOUT, ROOT
import sqlite3
import threading

_SWITCH_LOCK = threading.Lock()
_PREF_DB = ROOT / "model_selection.sqlite3"

def _pref_db():
    con = sqlite3.connect(_PREF_DB, timeout=10)
    con.execute("CREATE TABLE IF NOT EXISTS settings (name TEXT PRIMARY KEY, value TEXT NOT NULL)")
    return con

def _saved_model():
    with _pref_db() as con:
        row = con.execute("SELECT value FROM settings WHERE name=?", ("active_model",)).fetchone()
    return row[0] if row else ""

def _save_model(value):
    with _pref_db() as con:
        con.execute("INSERT INTO settings(name,value) VALUES(?,?) ON CONFLICT(name) DO UPDATE SET value=excluded.value", ("active_model", value))


def client():
    return OpenAI(base_url=BASE_URL, api_key=API_KEY, timeout=TIMEOUT, max_retries=1)

def list_models():
    return [item.id for item in client().models.list().data]

def _rest_request(path, payload=None):
    parsed = urlsplit(BASE_URL)
    if parsed.scheme != "http" or parsed.hostname not in ("127.0.0.1", "localhost", "::1") or parsed.username or parsed.password:
        raise RuntimeError("モデル管理はローカルのHTTP LM Studio APIのみ利用可能です")
    endpoint = f"{parsed.scheme}://{parsed.netloc}/api/v1/{path}"
    body = json.dumps(payload).encode("utf-8") if payload is not None else None
    req = Request(endpoint, data=body, method="POST" if body is not None else "GET")
    if body is not None:
        req.add_header("Content-Type", "application/json")
    if API_KEY and API_KEY != "lm-studio":
        req.add_header("Authorization", f"Bearer {API_KEY}")
    with urlopen(req, timeout=180 if body is not None else 10) as response:
        return json.load(response)

def local_models():
    return [m for m in _rest_request("models").get("models", []) if m.get("type") == "llm"]

def loaded_model_ids():
    ids = []
    for model in local_models():
        for instance in model.get("loaded_instances") or []:
            if instance.get("id"):
                ids.append(instance["id"])
    return ids


def switch_model(model_key, context_length=2048, kv_cache_on_gpu=False):
    """Switch only between installed local LLMs; no arbitrary model paths or URLs."""
    if not _SWITCH_LOCK.acquire(blocking=False):
        raise RuntimeError("別のモデル切り替えが進行中です")
    try:
        models = local_models()
        target = next((m for m in models if m.get("key") == model_key), None)
        if target is None:
            raise ValueError("LM Studioに登録されていないモデルです。モデル一覧を更新してください")
        context_length = int(context_length)
        if context_length not in (1024, 2048, 4096, 8192):
            raise ValueError("コンテキスト長は1024/2048/4096/8192のみ指定できます")
        # If already loaded, reuse it and do not disturb other models.
        existing = (target.get("loaded_instances") or [])
        if existing:
            instance_id = existing[0]["id"]
            _save_model(instance_id)
            return f"選択済み: {target.get('display_name', model_key)}\nID: {instance_id} (ロード済み)"
        # Memory-conscious switching: unload loaded LLM instances before loading target.
        for model in models:
            for instance in model.get("loaded_instances") or []:
                if instance.get("id"):
                    _rest_request("models/unload", {"instance_id": instance["id"]})
        _save_model("")  # never keep a stale model after unload
        result = _rest_request("models/load", {
            "model": model_key,
            "context_length": context_length,
            "flash_attention": True,
            "offload_kv_cache_to_gpu": bool(kv_cache_on_gpu),
            "echo_load_config": True,
        })
        instance_id = result.get("instance_id")
        if not instance_id or result.get("status") != "loaded":
            raise RuntimeError(f"モデルロードが完了しませんでした: {result}")
        _save_model(instance_id)
        return f"切り替え成功: {target.get('display_name', model_key)}\nID: {instance_id}\nContext: {context_length}"
    finally:
        _SWITCH_LOCK.release()

def selected_model():
    ids = loaded_model_ids()
    saved = _saved_model()
    if saved and saved in ids:
        return saved
    if MODEL_ID and MODEL_ID in ids:
        return MODEL_ID
    if len(ids) == 1:
        return ids[0]
    if not ids:
        raise RuntimeError('LM Studioにロード済みのLLMがありません。Model Connectionタブからロードしてください。')
    raise RuntimeError('複数モデルがロードされています。1モデルに絞るか.envでIDを指定してください: ' + ', '.join(ids))
