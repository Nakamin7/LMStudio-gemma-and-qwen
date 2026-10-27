# Changes in the Local + Cloud edition

This build extends the prior LM Studio model-switching version, without adding X/Twitter monitoring.

## Added

- `src/providers.py` — SQLite-backed inference provider selection and API-client routing (`local`, `openai`, `gemini`).
- `tests/test_providers.py` — mock-based provider, persistence, and agent dispatch tests.
- `docs/cloud-providers.md` — setup, API keys, privacy, billing, and troubleshooting.
- `docs/source-changes.md` — this change summary.

## Updated

- `src/agent.py` — resolve the provider and model at request start, dynamically; reuse the restricted tool schemas and append tool calls/results in Chat Completions format.
- `app.py` — Model Connection tab supports selection, model discovery, explicit save and cloud consent, while preserving LM Studio local load/unload controls.
- `.env.example` — add `OPENAI_API_KEY`, `GEMINI_API_KEY` placeholders.
- `README.md` — multi-provider usage and security notes.
- `docs/model-switching.md` — English-language model switching and provider switching instructions.
- `docs/configuration.md`, `docs/installation.md`, `docs/architecture.md`, `docs/operations.md`, `SECURITY.md` — multi-provider documentation.
- `.gitignore` — ignore `provider_selection.sqlite3*` (in addition to existing runtime and secret exclusions).
- `.github/workflows/ci.yml` — install full application dependencies, import the Gradio UI and run offline tests.

## Unchanged core

- `src/lmstudio.py` — local LM Studio REST switching.
- `src/database.py` and `src/rag.py` — tasks, run history, lexical document indexing.
- `src/scheduler.py` and `worker.py` — recurring worker: calls `src.agent.ask()` which dynamically resolves the current provider.
- `src/tools.py` — restricted tools (calculator, workspace reads and local document search).

## Selection flow

```text
app.py (Model Connection: choose + confirm + save)
   └── src.providers.set_provider(...)
         └── provider_selection.sqlite3

app.py (AI Chat) ── or ── worker.py (scheduled task)
   └── src.agent.ask(...)
         └── src.providers.resolve_inference()
               ├── local:  src.lmstudio.selected_model() and local OpenAI-compatible client
               ├── openai: OpenAI(api_key=OPENAI_API_KEY)
               └── gemini: OpenAI(api_key=GEMINI_API_KEY, base_url=Gemini OpenAI compatibility)
```

Cloud calls can send prompt/history/tool output to the provider and incur charges, including when the worker runs automatically. The app does not silently fall back to another provider.

## Migration

Copy the **changed or added files** from the update-only ZIP into your existing project root. **Do not delete or overwrite** your existing local `.env`, `agent.sqlite3`, `model_selection.sqlite3`, `data/documents/`, or workspace files. `provider_selection.sqlite3` is created automatically.

If you have modified source files, review and merge differences before overwriting them. Back up the project directory first.
<<<<<<< HEAD


## GraphRAG enhancement

- Added `src/graph_rag.py` for local entity-candidate extraction, source-grounded co-occurrence links, graph lookup, and hybrid retrieval.
- Added SQLite `graph_entities` and `graph_edges` tables.
- Document ingestion rebuilds the graph index for the changed source without sending text to any model or external service.
- `search_knowledge_base` merges graph evidence with FTS5 candidates before optional Jev relevance filtering.
- Added graph index status/rebuild controls to the Knowledge Base tab and offline tests.
- This initial version is deliberately lightweight; it does not claim semantic relationship extraction, embeddings, or full Microsoft GraphRAG functionality.
=======
>>>>>>> d113ef0042cbe2e6b1958bac71985936af2426c0
