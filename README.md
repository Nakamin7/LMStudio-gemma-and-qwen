<div align="center">

# LM Studio Agent — Local + Cloud

**Windows AI agent with LM Studio, OpenAI API, and Google Gemini API**

<<<<<<< HEAD
`Python 3.11` · `Gradio` · `SQLite FTS5` · `GraphRAG` · `optional vector RAG` · `mypy` · `pre-commit/Gitleaks`
=======
`Python` · `Gradio` · `SQLite FTS5` · `APScheduler`
>>>>>>> d113ef0042cbe2e6b1958bac71985936af2426c0

</div>

> [!IMPORTANT]
> Experimental project. **X/Twitter monitoring is not included.** Local model weights, API keys, personal files, SQLite databases, and logs are not distributed. This app binds the UI to localhost and is not designed for untrusted users or public deployment.

## Features

| Feature | Status |
| --- | --- |
| LM Studio local models (Gemma / Qwen GGUF) | Supported through OpenAI-compatible local API |
<<<<<<< HEAD
| OpenAI GPT models | Supported with `OPENAI_API_KEY`; Responses API is used for tool orchestration |
| Google Gemini models | Supported using the Gemini OpenAI-compatible API |
| Select provider and model from Web UI | Persistent SQLite preference shared with scheduled worker |
| LM Studio load / unload through Web UI | Preserved; stop the worker first |
| Chat and restricted tool calls | OpenAI uses Responses API; Gemini and LM Studio retain Chat Completions tools |
| Local TXT / MD / CSV search | SQLite FTS5, graph-assisted retrieval, optional vector retrieval |
=======
| OpenAI GPT models | Supported with `OPENAI_API_KEY` |
| Google Gemini models | Supported using the Gemini OpenAI-compatible API |
| Select provider and model from Web UI | Persistent SQLite preference shared with scheduled worker |
| LM Studio load / unload through Web UI | Preserved; stop the worker first |
| Chat and restricted tool calls | Supported on models implementing Chat Completions tools |
| Local TXT / MD / CSV search | SQLite FTS5 keyword search (not vector RAG) |
>>>>>>> d113ef0042cbe2e6b1958bac71985936af2426c0
| Scheduled tasks and run history | Separate `worker.py` process |
| Browser automation, unrestricted shell commands | Not included |

## Windows quick start

1. Install Python 3.11 and (for local inference) LM Studio.
2. In PowerShell, run:

```powershell
git clone https://github.com/Nakamin7/LMStudio-gemma-and-quen.git
cd LMStudio-gemma-and-quen
py -3.11 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
Copy-Item .env.example .env
```

3. **Local inference:** Start LM Studio and enable its local server at `http://127.0.0.1:1234`. Download and load one supported model.
4. **OpenAI:** Add `OPENAI_API_KEY` to `.env`, using an API key from the OpenAI Platform (not your ChatGPT password).
5. **Gemini:** Add `GEMINI_API_KEY` to `.env`, using a Gemini API key from Google AI Studio.
<<<<<<< HEAD
6. **OpenAI Responses API:** This project uses Responses API for OpenAI requests with tools. Ensure `openai>=1.66` is installed; Gemini and LM Studio continue using Chat Completions.

7. Start the UI and worker in **separate** terminals:
=======
6. Start the UI and worker in **separate** terminals:
>>>>>>> d113ef0042cbe2e6b1958bac71985936af2426c0

```powershell
.\start_ui.bat
# Open another terminal in the same folder:
.\start_worker.bat
```

<<<<<<< HEAD
8. Open `http://127.0.0.1:7860` → **Model Connection**. Select a provider, retrieve models, choose a compatible chat model, acknowledge cloud-data transfer and potential charges (for cloud providers), and click **Save Inference Target** (the UI may display this action in Japanese).
=======
7. Open `http://127.0.0.1:7860` → **Model Connection**. Select a provider, retrieve models, choose a compatible chat model, acknowledge cloud-data transfer and potential charges (for cloud providers), and click **Save Inference Target** (the UI may display this action in Japanese).
>>>>>>> d113ef0042cbe2e6b1958bac71985936af2426c0

Provider and model selection is stored in `provider_selection.sqlite3`, which is shared between the UI and worker. Model IDs for locally loaded LM Studio instances are stored separately in `model_selection.sqlite3`. **Changing a dropdown alone does not activate a model; press the save button.** Each new chat request or scheduled run reads the selected provider. No automatic cloud fallback is performed.

## Switching models using the Web UI

### Switch inference providers (LM Studio / OpenAI / Gemini)

1. Open **Model Connection**.
2. Select **LM Studio (local)**, **OpenAI API**, or **Google Gemini API**.
3. For online providers, click **Fetch Model List**, choose a supported model ID, and check the consent box.
4. Click **Save Inference Target**, then verify **Current Inference Target**.
5. Test the selection in **AI Chat**. The next scheduled task also uses the newly selected provider.

> **Privacy and costs:** When using an online provider, chat messages, recent history, system instructions, and tool outputs (including retrieved local document excerpts, if the model requests them) can be sent to that provider. Cloud API billing and rate limits apply separately from any ChatGPT subscription. Disable scheduled tasks before cloud switching if you want to avoid unattended billing.

### Switch locally loaded LM Studio models

1. Stop `start_worker.bat` and wait for active chat inference to finish.
2. In **Model Connection**, scroll to the LM Studio local model controls.
3. Refresh the downloaded model list, select the desired GGUF model, and choose the context length (start with `2048`; keep GPU KV cache off if VRAM is limited).
4. Check the confirmation box and click the local model switch button.
5. Save **LM Studio (local)** as the active provider and restart the worker.

<<<<<<< HEAD
See [Model Switching Guide](docs/model-switching.md) and [Cloud Provider Guide](docs/cloud-providers.md). For the OpenAI Responses API tool-call loop and its migration impact, see [Responses API Migration](docs/responses-api-migration.md).
=======
See [Model Switching Guide](docs/model-switching.md) and [Cloud Provider Guide](docs/cloud-providers.md).
>>>>>>> d113ef0042cbe2e6b1958bac71985936af2426c0

## Design

```text
                         ┌─────────────────┐
Gradio UI ───────────────>│                 │
                         │ Provider router │──── Local ── LM Studio / GGUF
APScheduler worker ──────>│   + SQLite      │──── OpenAI ─ OpenAI API
                         │                 │──── Gemini ─ Gemini API
                         └─────────────────┘
                                │
                         Allowlisted tools
                         (calculator / FTS5 / local text)
```

[Architecture](docs/architecture.md) · [Installation](docs/installation.md) · [Configuration](docs/configuration.md) · [Operations](docs/operations.md) · [Security](SECURITY.md)

## Security and limitations

- **Never commit `.env` or API keys.** `.gitignore` does not remove secrets already in Git history.
- ChatGPT website subscriptions and OpenAI API access are **separate products**. This integrates **OpenAI API**, not automated ChatGPT website access.
- API models can have different tool-calling capabilities; model listing does not guarantee Chat Completions or tool compatibility.
- Switching to cloud inference affects **future scheduled executions**, which can incur charges.
- The local UI has no multi-user authentication. Keep it bound to `127.0.0.1`.
- Automatic tasks only run while the worker and PC are running.
- Generated results may be inaccurate and tool calls must remain allowlisted.

<<<<<<< HEAD
## Tests and static type checking

Install development checks and run them from the project root:

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements-dev.txt
.\.venv\Scripts\python.exe -m pytest -q
.\.venv\Scripts\python.exe -m mypy --config-file mypy.ini
```

Production Python functions have parameter and return annotations. `mypy.ini` enables checking of untyped function bodies and rejects unannotated function signatures in the configured application paths. SDK/network/database boundaries may use `Any` where third-party response schemas are dynamic; prefer concrete types when extending those paths. The pre-commit hook and CI workflow run the type checker.


=======
## Tests

```powershell
.\.venv\Scripts\python.exe -m pip install pytest
.\.venv\Scripts\python.exe -m pytest -q
```

>>>>>>> d113ef0042cbe2e6b1958bac71985936af2426c0
These tests mock model APIs and do not perform live billing or GPU inference.

## License

MIT license for this project's source code; model weights and third-party libraries have their own licenses.

## Optional Jev relevance filtering

Jev integration is opt-in and disabled by default. See [`docs/jev-integration.md`](docs/jev-integration.md) for the external-data disclosure, consent steps, permission boundary, and setup. Set `TYPESAFE_API_KEY` in your local `.env`, then explicitly enable Jev and accept the Jev-specific disclosure in **Model Connection**. This sends the search query and bounded excerpts of retrieved passages to TypeSafe AI. Do not enable it for sensitive documents unless external processing is approved. Jev does not receive or execute app tools, and its output cannot authorize file/configuration changes. The feature falls back to local search if the Jev API fails.
<<<<<<< HEAD


## GraphRAG quality improvements

The Knowledge Base supports local graph-assisted retrieval, optional local-LM semantic relation extraction, and offline retrieval evaluation. See [`docs/graphrag.md`](docs/graphrag.md), [`docs/improvement-release-notes.md`](docs/improvement-release-notes.md), and [`evaluation/README.md`](evaluation/README.md). Build a verified evaluation set before drawing conclusions about answer-quality improvements.


## Enhanced retrieval

Optional vector search is provided through the LM Studio OpenAI-compatible embeddings endpoint. Set `EMBEDDING_MODEL` in `.env` to the exact loaded embedding model ID and rebuild the vector index from Knowledge Base. Without this setting, lexical and graph retrieval remain available. See `docs/operations.md` for local testing, relation-extraction evaluation, and citation checks.

## Git pre-commit secret protection

Install the repository's Gitleaks hook after cloning so commits containing detected API keys or other secrets are rejected:

```powershell
py -3.11 -m pip install -r requirements-dev.txt
.\.venv\Scripts\pre-commit.exe install
.\.venv\Scripts\pre-commit.exe run --all-files
```

The hook uses `.gitleaks.toml` and Gitleaks' built-in detectors. GitHub Actions also scans pushes and pull requests. This hook must be installed separately in each clone; never commit a real API key, and rotate any credential that has already been exposed.

## Type hints and mypy

- Type-check configuration: [`mypy.ini`](mypy.ini).
- All function definitions in `src/`, `app.py`, `config.py`, `worker.py`, and `evaluation/` have parameter and return annotations; dynamic third-party SDK responses use `Any` at the boundary.
- Run `python -m mypy --config-file mypy.ini` before committing. The pre-commit hook checks this automatically after installation.
=======
>>>>>>> d113ef0042cbe2e6b1958bac71985936af2426c0
