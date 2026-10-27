# Operations and Troubleshooting

- Start Gradio UI using `start_ui.bat` and the scheduler worker using `start_worker.bat`.
- Stop each process with `Ctrl+C`. Avoid running multiple scheduler workers.
- **Switch active provider:** Use **Model Connection**, fetch available model IDs for cloud APIs, and **save** the selection. The next chat or scheduled task reads it.
- **Switch local LM Studio models:** stop the worker and active inference; perform local unload/load from the UI; restart the worker.
- **Changing API keys:** edit `.env` and restart both UI and worker processes.
- **Model not found / unsupported tools:** confirm that the model supports Chat Completions with function calling.
- **Cloud API 401 / 403 / 429:** check API key, project/billing entitlement, and usage limits.
- **LM Studio memory error:** unload other models, reduce context length or GPU offload; do not bypass memory safeguards.
- **Missing `lms`:** use LM Studio GUI or the native local REST API switch UI.
- **Scheduled costs:** when a cloud provider is selected, scheduled tasks can automatically incur API usage charges. Pause tasks when not needed.
- **Document search:** hybrid SQLite FTS5 + local graph-assisted retrieval. Japanese lexical search can still be weak; graph matches are lexical entity candidates and co-occurrence evidence, not verified semantic relations.
- **Graph index:** new uploads update the graph automatically. Use Knowledge Base → GraphRAG index rebuild after changing indexing behavior or recovering an inconsistent graph index.

See [Cloud Provider Guide](cloud-providers.md).


## ベクトル検索の設定と実機検証

1. LM Studio で埋め込みに対応したモデルをダウンロード・ロードします。
2. `.env` の `EMBEDDING_MODEL` に LM Studio の API が返す正確なモデル ID を設定します。チャット用モデル ID と同じとは限りません。
3. アプリを再起動し、Knowledge Base タブで「ベクトル索引を構築 / 更新」を実行します。
4. 検索結果に `検索戦略` と `検索経路` が表示されることを確認します。埋め込み API が未対応の場合、ログ/表示でエラーを確認し、空欄に戻せば従来検索にフォールバックします。

## テスト手順（Windows PowerShell）

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
python -m pytest -q
```

pytest が requirements に含まれていない環境では `pip install pytest` も実行してください。全テストの失敗を無視せず、エラーの先頭スタックと対象テスト名を記録します。

## 関係抽出の品質評価

`evaluation/gold_relations.json` を作成し、手作業で正しいと確認した関係を記録します。形式例:

```json
[
  {"source":"src/agent.py","relation":"calls","target":"src/tools.py"}
]
```

先に Knowledge Base で「ローカルLLMで意味的関係を抽出」を実行し、その後に `python -m evaluation.evaluate_relations evaluation/gold_relations.json` を実行します。Precision、Recall、F1 と誤検出・見逃しが表示されます。評価用の gold はモデル出力をそのまま正解にせず、人が原文と照合してください。

## 回答の根拠検証

ナレッジ検索を使った回答には `[出典: ファイル名]` が必要です。アプリは引用された出典が検索結果に含まれるかを機械的に確認し、不一致や引用欠落に警告を付けます。これは出典の存在確認であり、回答中の全ての主張が真実であることを保証するものではありません。重要な回答は引用箇所を原文と照合してください。
