from src.database import init_db, add_task, tasks, set_enabled

def test_task_lifecycle(tmp_path, monkeypatch):
    import src.database as db
    monkeypatch.setattr(db, 'DB_PATH', tmp_path / 'test.sqlite3')
    init_db()
    task_id = add_task('demo', 'Summarize local notes', 60)
    assert any(t['id'] == task_id for t in tasks())
    set_enabled(task_id, False)
    assert next(t for t in tasks() if t['id'] == task_id)['enabled'] == 0
