import sqlite3
from datetime import datetime, timezone
from config import DB_PATH

def now():
    return datetime.now(timezone.utc).isoformat()

def connect():
    conn = sqlite3.connect(DB_PATH, timeout=30)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA busy_timeout=30000")
    return conn

def init_db():
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

def add_task(name, prompt, interval_minutes):
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

def tasks():
    with connect() as db:
        return [dict(row) for row in db.execute("SELECT * FROM tasks ORDER BY id DESC")]

def set_enabled(task_id, enabled):
    with connect() as db:
        cursor = db.execute("UPDATE tasks SET enabled=? WHERE id=?", (int(bool(enabled)), int(task_id)))
        if not cursor.rowcount:
            raise ValueError("指定されたタスクがありません")

def runs(limit=30):
    with connect() as db:
        return [dict(row) for row in db.execute("SELECT * FROM runs ORDER BY id DESC LIMIT ?", (limit,))]

def record_run(task_id, started_at, status, result):
    with connect() as db:
        db.execute("INSERT INTO runs(task_id,started_at,finished_at,status,result) VALUES(?,?,?,?,?)",
                   (task_id,started_at,now(),status,result[:20000]))
