<<<<<<< HEAD
from typing import Any
=======
>>>>>>> d113ef0042cbe2e6b1958bac71985936af2426c0
import sqlite3
from datetime import datetime, timezone
from config import DB_PATH

<<<<<<< HEAD
def now() -> Any:
    return datetime.now(timezone.utc).isoformat()

def connect() -> Any:
=======
def now():
    return datetime.now(timezone.utc).isoformat()

def connect():
>>>>>>> d113ef0042cbe2e6b1958bac71985936af2426c0
    conn = sqlite3.connect(DB_PATH, timeout=30)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA busy_timeout=30000")
    return conn

<<<<<<< HEAD
def init_db() -> Any:
=======
def init_db():
>>>>>>> d113ef0042cbe2e6b1958bac71985936af2426c0
    with connect() as db:
        db.execute("PRAGMA journal_mode=WAL")
        db.execute("""CREATE TABLE IF NOT EXISTS tasks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL, prompt TEXT NOT NULL,
            interval_minutes INTEGER NOT NULL,
            enabled INTEGER NOT NULL DEFAULT 1,
            created_at TEXT NOT NULL)""")
        db.execute("""CREATE TABLE IF NOT EXISTS runs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            task_id INTEGER NOT NULL,
            started_at TEXT NOT NULL,
            finished_at TEXT NOT NULL,
            status TEXT NOT NULL,
            result TEXT NOT NULL)""")
        db.execute("""CREATE VIRTUAL TABLE IF NOT EXISTS documents_fts
            USING fts5(source UNINDEXED, content, tokenize='unicode61')""")
<<<<<<< HEAD
        # Local, source-grounded graph index. Relationships are co-occurrence links,
        # not claims of semantic causation; every edge retains its evidence excerpt.
        db.execute("""CREATE TABLE IF NOT EXISTS graph_entities (
            entity TEXT NOT NULL,
            source TEXT NOT NULL,
            chunk_id INTEGER NOT NULL,
            excerpt TEXT NOT NULL,
            PRIMARY KEY(entity, source, chunk_id)
        )""")
        db.execute("""CREATE TABLE IF NOT EXISTS graph_edges (
            source TEXT NOT NULL,
            target TEXT NOT NULL,
            relation TEXT NOT NULL,
            document_source TEXT NOT NULL,
            chunk_id INTEGER NOT NULL,
            evidence TEXT NOT NULL,
            PRIMARY KEY(source, target, relation, document_source, chunk_id)
        )""")
        db.execute("CREATE INDEX IF NOT EXISTS idx_graph_entities_entity ON graph_entities(entity)")
        db.execute("CREATE INDEX IF NOT EXISTS idx_graph_edges_source ON graph_edges(source)")
        # Embedding vectors are stored as JSON to keep the base install dependency-light.
        db.execute("""CREATE TABLE IF NOT EXISTS document_vectors (
            chunk_id INTEGER PRIMARY KEY,
            source TEXT NOT NULL,
            content_hash TEXT NOT NULL,
            model TEXT NOT NULL,
            dimensions INTEGER NOT NULL,
            vector_json TEXT NOT NULL,
            updated_at TEXT NOT NULL
        )""")
        db.execute("CREATE INDEX IF NOT EXISTS idx_document_vectors_model ON document_vectors(model)")
        # Ground-truth relation annotations used to evaluate extraction precision/recall.
        db.execute("""CREATE TABLE IF NOT EXISTS relation_gold (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            source TEXT NOT NULL,
            subject TEXT NOT NULL,
            relation TEXT NOT NULL,
            object TEXT NOT NULL,
            evidence TEXT NOT NULL DEFAULT ''
        )""")

def add_task(name: Any, prompt: Any, interval_minutes: Any) -> Any:
=======

def add_task(name, prompt, interval_minutes):
>>>>>>> d113ef0042cbe2e6b1958bac71985936af2426c0
    name, prompt = name.strip(), prompt.strip()
    if not name or not prompt:
        raise ValueError("タスク名と指示が必要です")
    if interval_minutes is None or isinstance(interval_minutes, bool):
        raise ValueError('実行間隔を入力してください')
    interval = int(interval_minutes)
    if float(interval_minutes) != interval:
        raise ValueError('実行間隔は整数で指定してください')
    if interval < 5 or interval > 10080:
        raise ValueError("実行間隔は5〜10080分です")
    with connect() as db:
        cursor = db.execute("INSERT INTO tasks(name,prompt,interval_minutes,created_at) VALUES(?,?,?,?)",
                            (name,prompt,interval,now()))
        return cursor.lastrowid

<<<<<<< HEAD
def tasks() -> Any:
    with connect() as db:
        return [dict(row) for row in db.execute("SELECT * FROM tasks ORDER BY id DESC")]

def set_enabled(task_id: Any, enabled: Any) -> Any:
=======
def tasks():
    with connect() as db:
        return [dict(row) for row in db.execute("SELECT * FROM tasks ORDER BY id DESC")]

def set_enabled(task_id, enabled):
>>>>>>> d113ef0042cbe2e6b1958bac71985936af2426c0
    with connect() as db:
        cursor = db.execute("UPDATE tasks SET enabled=? WHERE id=?", (int(bool(enabled)), int(task_id)))
        if not cursor.rowcount:
            raise ValueError("指定されたタスクがありません")

<<<<<<< HEAD
def runs(limit: Any = 30) -> Any:
    with connect() as db:
        return [dict(row) for row in db.execute("SELECT * FROM runs ORDER BY id DESC LIMIT ?", (limit,))]

def record_run(task_id: Any, started_at: Any, status: Any, result: Any) -> Any:
=======
def runs(limit=30):
    with connect() as db:
        return [dict(row) for row in db.execute("SELECT * FROM runs ORDER BY id DESC LIMIT ?", (limit,))]

def record_run(task_id, started_at, status, result):
>>>>>>> d113ef0042cbe2e6b1958bac71985936af2426c0
    with connect() as db:
        db.execute("INSERT INTO runs(task_id,started_at,finished_at,status,result) VALUES(?,?,?,?,?)",
                   (task_id,started_at,now(),status,result[:20000]))
