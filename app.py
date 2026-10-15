from pathlib import Path
import shutil
import gradio as gr
from config import DOCUMENTS
from src.database import init_db, add_task, tasks, set_enabled, runs
from src.rag import ingest_file, index_documents
from src.agent import ask
from src.lmstudio import list_models, selected_model, local_models, switch_model
from ui.theme import get_theme

init_db()
CSS = (Path(__file__).parent / 'ui' / 'custom.css').read_text(encoding='utf-8')

def chat(message, history):
    try:
        return ask(message, history)
    except Exception as exc:
        return f'エラー: {type(exc).__name__}: {exc}'

def register_file(file_path):
    if not file_path:
        return 'ファイルを選択してください'
    try:
        path = Path(file_path)
        if path.suffix.lower() not in {'.txt', '.md', '.csv'}:
            raise ValueError('未対応の形式です')
        if path.stat().st_size > 2_000_000:
            raise ValueError('2MBを超えています')
        destination = DOCUMENTS / path.name
        if path.resolve() != destination.resolve():
            shutil.copy2(path, destination)
        return f'{destination.name}: {ingest_file(destination)}件登録しました'
    except Exception as exc:
        return f'登録エラー: {type(exc).__name__}: {exc}'

def format_tasks():
    rows = tasks()
    return '\n'.join(f"#{x['id']} | {'有効' if x['enabled'] else '停止'} | {x['interval_minutes']}分 | {x['name']}" for x in rows) or 'タスクなし'

def add_task_ui(name, prompt, interval):
    try:
        task_id = add_task(name, prompt, interval)
        return f'タスク #{task_id} を登録しました。ワーカーが30秒以内に検知します。', format_tasks()
    except Exception as exc:
        return f'登録エラー: {type(exc).__name__}: {exc}', format_tasks()

def update_task(task_id, enabled):
    try:
        if task_id is None:
            raise ValueError('タスクIDを入力してください')
        set_enabled(int(task_id), enabled)
        return '更新しました。\n' + format_tasks()
    except Exception as exc:
        return f'エラー: {type(exc).__name__}: {exc}'

def format_runs():
    rows = runs()
    return '\n\n'.join(f"#{x['task_id']} [{x['status']}] {x['finished_at']}\n{x['result'][:1000]}" for x in rows) or '実行履歴なし'

def model_status():
    try:
        models = local_models()
        active = [f"{m.get('display_name',m['key'])}: {i['id']}" for m in models for i in m.get('loaded_instances', [])]
        selected = selected_model() if active else "なし"
        return f"選択中: {selected}\nロード済み: " + (" / ".join(active) if active else "なし")
    except Exception as exc:
        return f"接続エラー: {type(exc).__name__}: {exc}"

def model_choices():
    try:
        models = local_models()
        options = [(m.get('display_name') or m['key'], m['key']) for m in models]
        return gr.update(choices=options, value=None), model_status()
    except Exception as exc:
        return gr.update(choices=[], value=None), f"一覧取得エラー: {type(exc).__name__}: {exc}"

def apply_model_switch(model_key, context_length, kv_cache_on_gpu, confirmed):
    if not confirmed:
        return "切り替えを実行するには確認チェックを入れてください。", model_status()
    if not model_key:
        return "モデルを選択してください。", model_status()
    try:
        result = switch_model(model_key, context_length, kv_cache_on_gpu)
        return result, model_status()
    except Exception as exc:
        return f"切り替え失敗: {type(exc).__name__}: {exc}", model_status()

with gr.Blocks(title='LM Studio Agent', theme=get_theme(), css=CSS) as demo:
    # Single HTML dashboard: stable three-column layout and explicit text contrast.
    gr.HTML("""
    <div class="agent-dashboard">
      <header class="agent-hero">
        <p class="agent-eyebrow">LOCAL-FIRST AI WORKSPACE</p>
        <h1>LM Studio Agent</h1>
        <p class="agent-description">Private inference · Restricted tools · Scheduled workflows</p>
      </header>
      <section class="agent-grid" aria-label="Workspace overview">
        <article class="agent-card">
          <p class="agent-card-label">INFERENCE</p>
          <p class="agent-card-value">LM Studio</p>
          <p class="agent-card-detail">Local API · 127.0.0.1</p>
        </article>
        <article class="agent-card">
          <p class="agent-card-label">MODEL</p>
          <p class="agent-card-value">Gemma / Qwen</p>
          <p class="agent-card-detail">One model at a time · check status below</p>
        </article>
        <article class="agent-card">
          <p class="agent-card-label">STORAGE</p>
          <p class="agent-card-value">SQLite FTS5</p>
          <p class="agent-card-detail">Local documents &amp; tasks</p>
        </article>
      </section>
    </div>
    """)
    with gr.Tabs():
        with gr.Tab('AI Chat'):
            gr.ChatInterface(fn=chat)
        with gr.Tab('Knowledge Base'):
            gr.Markdown('### ローカル文書を登録\nTXT / MD / CSV、最大2MB。登録内容はローカルDBに保存されます。')
            upload = gr.File(label='Document', type='filepath', file_types=['.txt', '.md', '.csv'])
            upload_btn = gr.Button('Add Document', variant='primary')
            upload_result = gr.Textbox(label='Result')
            upload_btn.click(fn=register_file, inputs=upload, outputs=upload_result)
        with gr.Tab('Automations'):
            gr.Markdown('### Scheduled Tasks\nワーカーを別プロセスで起動してください。')
            name = gr.Textbox(label='タスク名')
            prompt = gr.Textbox(label='実行指示', lines=4)
            interval = gr.Number(label='実行間隔（分）', value=60, minimum=5, maximum=10080, precision=0)
            create = gr.Button('Register Task', variant='primary')
            status = gr.Textbox(label='登録結果')
            listing = gr.Textbox(label='タスク一覧', lines=8, value=format_tasks())
            create.click(fn=add_task_ui, inputs=[name, prompt, interval], outputs=[status, listing])
            gr.Button('Refresh Tasks').click(fn=format_tasks, outputs=listing)
            task_id = gr.Number(label='変更するタスクID', precision=0)
            enabled = gr.Checkbox(label='有効にする', value=True)
            gr.Button('Apply Status').click(fn=update_task, inputs=[task_id, enabled], outputs=listing)
        with gr.Tab('Run History'):
            history_box = gr.Textbox(label='直近の実行結果', lines=16)
            gr.Button('Refresh History').click(fn=format_runs, outputs=history_box)
        with gr.Tab('Model Connection'):
            gr.Markdown('### ローカルLLMモデル切り替え\nLM Studioでダウンロード済みのLLMのみ表示します。切り替え前に **worker.pyを停止** し、進行中のチャットがないことを確認してください。ロード時は現在のLLMをアンロードします。')
            model_box = gr.Textbox(label='LM Studio接続状態', lines=4, value='「モデル一覧を更新」を押してください。')
            model_dropdown = gr.Dropdown(label='切り替え先モデル', choices=[], interactive=True)
            gr.Button('モデル一覧を更新').click(fn=model_choices, outputs=[model_dropdown, model_box])
            context = gr.Dropdown(label='コンテキスト長', choices=[1024, 2048, 4096, 8192], value=2048)
            kv_cache = gr.Checkbox(label='KVキャッシュをGPUに配置する（VRAM使用量が増加します）', value=False)
            confirmed = gr.Checkbox(label='ワーカーを停止し、実行中の推論がないことを確認しました', value=False)
            switch_button = gr.Button('選択したモデルに切り替える', variant='primary')
            switch_result = gr.Textbox(label='切り替え結果', lines=4)
            switch_button.click(fn=apply_model_switch, inputs=[model_dropdown, context, kv_cache, confirmed], outputs=[switch_result, model_box], concurrency_limit=1)
            gr.Button('接続状態を再確認').click(fn=model_status, outputs=model_box)

if __name__ == '__main__':
    index_documents()
    demo.launch(server_name='127.0.0.1', server_port=7860, share=False)
