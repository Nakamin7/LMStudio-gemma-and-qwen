from typing import Any
import threading
from apscheduler.schedulers.blocking import BlockingScheduler
from src.database import init_db, connect, now, record_run
from src.agent import ask

scheduler=BlockingScheduler(timezone='Asia/Tokyo',job_defaults={'max_instances':1,'coalesce':True})
lock=threading.Lock()

def execute(task_id: Any) -> Any:
    if not lock.acquire(blocking=False):
        return
    started=now()
    try:
        with connect() as db:
            row=db.execute('SELECT prompt,enabled FROM tasks WHERE id=?',(task_id,)).fetchone()
        if not row or not row['enabled']: return
        try:
            result=ask(row['prompt'])
            record_run(task_id,started,'ok',result)
        except Exception as exc:
            record_run(task_id,started,'error',f'{type(exc).__name__}: {exc}')
    finally:
        lock.release()

def sync_jobs() -> Any:
    with connect() as db:
        tasks=[dict(row) for row in db.execute('SELECT * FROM tasks WHERE enabled=1')]
    current={f"task_{t['id']}" for t in tasks}
    for job in scheduler.get_jobs():
        if job.id.startswith('task_') and job.id not in current:
            scheduler.remove_job(job.id)
    for task in tasks:
        job_id=f"task_{task['id']}"
        old=scheduler.get_job(job_id)
        if old and old.trigger.interval.total_seconds()==task['interval_minutes']*60:
            continue
        scheduler.add_job(execute,'interval',minutes=task['interval_minutes'],args=[task['id']],id=job_id,replace_existing=True)

def main() -> Any:
    init_db()
    sync_jobs()
    scheduler.add_job(sync_jobs,'interval',seconds=30,id='sync',max_instances=1)
    print('常駐ワーカー起動: Ctrl+Cで終了')
    scheduler.start()
