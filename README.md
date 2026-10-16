<div align="center">

# LM Studio Agent — Local + Cloud

**Windows AI agent with LM Studio, OpenAI API, and Google Gemini API**

`Python` · `Gradio` · `SQLite FTS5` · `APScheduler`

</div>

> [!IMPORTANT]
> Experimental project. **X/Twitter monitoring is not included.** Local model weights, API keys, personal files, SQLite databases, and logs are not distributed. This app binds the UI to localhost and is not designed for untrusted users or public deployment.

## Features

| Feature | Status |
| --- | --- |
| LM Studio local models (Gemma / Qwen GGUF) | Supported through OpenAI-compatible local API |
| OpenAI GPT models | Supported with `OPENAI_API_KEY` |
| Google Gemini models | Supported using the Gemini OpenAI-compatible API |
| Select provider and model from Web UI | Persistent SQLite preference shared with scheduled worker |
| LM Studio load / unload through Web UI | Preserved; stop the worker first |
| Chat and restricted tool calls | Supported on models implementing Chat Completions tools |
| Local TXT / MD / CSV search | SQLite FTS5 keyword search (not vector RAG) |
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
6. Start the UI and worker in **separate** terminals:

```powershell
.\start_ui.bat
# Open another terminal in the same folder:
.\start_worker.bat
```

7. Open `http://127.0.0.1:7860` → **Model Connection**. Select a provider, retrieve models, choose a compatible chat model, acknowledge cloud-data transfer and potential charges (for cloud providers), and click **Save Inference Target** (the UI may display this action in Japanese).

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

See [Model Switching Guide](docs/model-switching.md) and [Cloud Provider Guide](docs/cloud-providers.md).

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

## Tests

```powershell
.\.venv\Scripts\python.exe -m pip install pytest
.\.venv\Scripts\python.exe -m pytest -q
```

These tests mock model APIs and do not perform live billing or GPU inference.

## License

MIT license for this project's source code; model weights and third-party libraries have their own licenses.

## Optional Jev relevance filtering

Jev integration is opt-in and disabled by default. See [`docs/jev-integration.md`](docs/jev-integration.md) for the external-data disclosure, consent steps, permission boundary, and setup. Set `TYPESAFE_API_KEY` in your local `.env`, then explicitly enable Jev and accept the Jev-specific disclosure in **Model Connection**. This sends the search query and bounded excerpts of retrieved passages to TypeSafe AI. Do not enable it for sensitive documents unless external processing is approved. Jev does not receive or execute app tools, and its output cannot authorize file/configuration changes. The feature falls back to local search if the Jev API fails.
