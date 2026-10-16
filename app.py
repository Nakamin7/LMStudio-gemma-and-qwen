from pathlib import Path
import shutil
import gradio as gr
from config import DOCUMENTS
from src.database import init_db, add_task, tasks, set_enabled, runs
from src.rag import ingest_file, index_documents
from src.agent import ask
from src.lmstudio import selected_model, local_models, switch_model
from src.providers import (current_selection, list_provider_models, set_provider,
                           selection_status, jev_preferences, set_jev_preferences)
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


def provider_models(provider):
    if provider == 'local':
        return gr.update(choices=[], value=None), 'LM Studioのモデルは下の「モデル一覧を更新」から読み込み・切り替えしてください。'
    try:
        items = list_provider_models(provider)
        if not items:
            return gr.update(choices=[], value=None), "利用可能なチャットモデルが見つかりません。API権限またはモデル設定を確認してください。"
        previous_provider, previous_model = current_selection()
        preferred = previous_model if previous_provider == provider and previous_model in items else items[0]
        return gr.update(choices=items, value=preferred), f"{provider}: {len(items)} 件のモデルIDを取得しました。モデルによってはChat Completionsに非対応です。"
    except Exception as exc:
        return gr.update(choices=[], value=None), f"一覧取得エラー: {type(exc).__name__}: {exc}"


def provider_changed(provider):
    # Changing a dropdown never changes what the worker uses. Explicit save is required.
    return gr.update(choices=[], value=None), f"{provider} を選択中です。「モデル一覧を取得」を押してください。"


def save_jev_settings(enabled, consented):
    try:
        message = set_jev_preferences(enabled, consented)
        if enabled and not __import__("os").getenv("TYPESAFE_API_KEY", "").strip():
            return message + "。ただし TYPESAFE_API_KEY が未設定のため、判定時にローカル検索へフォールバックします。", jev_preferences()[0], jev_preferences()[1]
        return message, jev_preferences()[0], jev_preferences()[1]
    except Exception as exc:
        current_enabled, current_consent = jev_preferences()
        return f"設定エラー: {type(exc).__name__}: {exc}", current_enabled, current_consent


def apply_provider(provider, model, cloud_confirmed):
    try:
        result = set_provider(provider, model or "", cloud_confirmed=cloud_confirmed)
        return result, selection_status()
    except Exception as exc:
        return f"設定エラー: {type(exc).__name__}: {exc}", selection_status()


with gr.Blocks(title='LM Studio Agent') as demo:
    # Single HTML dashboard: stable three-column layout and explicit text contrast.
    gr.HTML("""
    <div class="agent-dashboard">
      <header class="agent-hero">
        <p class="agent-eyebrow">LOCAL + CLOUD AI WORKSPACE</p>
        <h1>LM Studio Agent</h1>
        <p class="agent-description">Select local or cloud inference · Restricted tools · Scheduled workflows</p>
      </header>
      <section class="agent-grid" aria-label="Workspace overview">
        <article class="agent-card">
          <p class="agent-card-label">INFERENCE</p>
          <p class="agent-card-value">3 providers</p>
          <p class="agent-card-detail">LM Studio · OpenAI · Gemini</p>
        </article>
        <article class="agent-card">
          <p class="agent-card-label">MODEL</p>
          <p class="agent-card-value">Local + Cloud</p>
          <p class="agent-card-detail">Explicit selection · no fallback</p>
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
            gr.Markdown('### 推論プロバイダーとモデルの選択\n**LM Studio / OpenAI API / Gemini API** に切り替えられます。設定はチャットとワーカーで共有されます。**オンラインを選ぶと質問・履歴・ツール結果が外部APIへ送信され、API利用料金が発生する場合があります。**')
            saved_provider, saved_model = current_selection()
            provider_pick = gr.Dropdown(
                label='推論プロバイダー',
                choices=[('LM Studio (local)', 'local'), ('OpenAI API (GPT)', 'openai'), ('Google Gemini API', 'gemini')],
                value=saved_provider,
                interactive=True,
            )
            online_model = gr.Dropdown(
                label='オンラインモデルID（候補から選択、または手入力）',
                choices=[saved_model] if saved_provider != 'local' and saved_model else [],
                value=saved_model if saved_provider != 'local' and saved_model else None,
                interactive=True,
                allow_custom_value=True,
            )
            provider_hint = gr.Textbox(label='モデル一覧の取得結果', value='「モデル一覧を取得」で接続と利用可能モデルを確認できます。', lines=2)
            provider_pick.change(fn=provider_changed, inputs=provider_pick, outputs=[online_model, provider_hint])
            gr.Button('モデル一覧を取得（オンラインの場合はAPIへの接続が必要）').click(
                fn=provider_models, inputs=provider_pick, outputs=[online_model, provider_hint],
            )
            online_confirm = gr.Checkbox(label='オンラインAPIへのデータ送信と従量課金の可能性を理解しました（オンライン選択時のみ必須）', value=False)
            provider_result = gr.Textbox(label='保存結果', lines=2)
            active_provider_box = gr.Textbox(label='現在の推論先（チャット・ワーカー共通）', value=selection_status(), lines=4)
            gr.Button('この推論先を保存', variant='primary').click(
                fn=apply_provider,
                inputs=[provider_pick, online_model, online_confirm],
                outputs=[provider_result, active_provider_box],
                concurrency_limit=1,
            )
            gr.Button('現在の推論先を再確認').click(fn=selection_status, outputs=active_provider_box)
            gr.Markdown('''---
### Jevによるナレッジ検索の関連度判定（任意・初期状態は無効）
Jevは検索候補の関連度を判定するためだけに利用します。Jevへ送信されるのは、ナレッジ検索の質問（最大2,000文字）、候補文書名（最大160文字）、候補本文の抜粋（最大1,200文字、最大4件）です。Jevにはファイル操作ツール、ローカルファイルシステム、他のAPIキーを渡しません。

Jevは外部サービスです。入力がTypeSafe AIのAPIへ送信され、料金・利用制限・データ取扱いが適用されます。機密情報や個人情報を含む文書は、送信の適法性と必要性を確認してから利用してください。Jevの判定が失敗した場合はローカル検索結果にフォールバックします。Jevの判定はファイル削除、読み取り、設定変更などの権限を付与しません。

利用前に [TypeSafe AI](https://typesafe.ai/) と [Jev開発ドキュメント](https://docs.typesafe.ai/) の最新の利用規約、プライバシー説明、料金、制限を確認してください。JevのAPIキーは `.env` の `TYPESAFE_API_KEY` に設定します。
''')
            jev_enabled_saved, jev_consent_saved = jev_preferences()
            jev_enabled = gr.Checkbox(label='Jevの関連度判定を有効にする', value=jev_enabled_saved)
            jev_consent = gr.Checkbox(label='質問と検索候補の抜粋がJev（TypeSafe AI）の外部APIへ送信されること、利用条件・料金を確認しました', value=jev_consent_saved)
            jev_status = gr.Textbox(label='Jev設定結果', lines=2, value='Jevは初期状態では無効です。')
            gr.Button('Jev設定を保存').click(fn=save_jev_settings, inputs=[jev_enabled, jev_consent], outputs=[jev_status, jev_enabled, jev_consent], concurrency_limit=1)
            gr.Markdown('---\n### LM Studio ローカルモデルの読み込み・切り替え\n**ローカルモデルのロード/アンロード専用**です。切り替え前にworker.pyを停止し、進行中のチャットがないことを確認してください。オンラインAPI利用時にはこの操作は必要ありません。')
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
    demo.launch(server_name='127.0.0.1', server_port=7860, share=False, theme=get_theme(), css=CSS)
