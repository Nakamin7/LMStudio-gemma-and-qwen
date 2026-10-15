<div align="center">

# LM Studio Agent

**Local-first AI workspace for Windows**

Chat with a local model · Search your documents · Run scheduled tasks

`LM Studio` · `Python` · `Gradio` · `SQLite FTS5` · `APScheduler`

</div>

> [!IMPORTANT]
> **Experimental project.** This repository contains source code, not GGUF weights. The two named model variants are *candidate models*, not verified compatibility claims. Test tool calling and memory use on your own machine. Do not expose the local UI or API to untrusted networks.

## Features

| Feature | Status |
| --- | --- |
| LM Studio OpenAI-compatible inference | Implemented |
| Local chat and restricted tool calling | Implemented; model-dependent |
| TXT / MD / CSV document indexing | Implemented (SQLite FTS5 lexical search, **not vector RAG**) |
| Scheduled tasks and local execution history | Implemented (separate worker process) |
| Gemma / Qwen switching | Manual via LM Studio or `switch_model.ps1` |
| Browser automation / arbitrary shell execution | **Not included** |
| Remote access / multi-user authentication | **Not included** |

## Interface

The Gradio dashboard uses a dark, minimal workspace style with Chat, Knowledge Base, Automations, Run History and Model Connection tabs. **No screenshot is bundled until a real, redacted capture is available.**

## Quick start (Windows / PowerShell)

1. Install [Python 3.11](https://www.python.org/downloads/) and [LM Studio](https://lmstudio.ai/).
2. Clone and install:

```powershell
git clone https://github.com/YOUR_USERNAME/LMStudio-gemma-and-quen.git
cd LMStudio-gemma-and-quen
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
Copy-Item .env.example .env
```

3. In LM Studio, download and load **one** compatible model and start its local server on port `1234`. Because memory estimates can exceed 16 GB, try context length `2048` and adjust GPU offload cautiously. Do **not** disable memory guardrails to force a load.
4. Check the available model IDs:

```powershell
(Invoke-RestMethod http://127.0.0.1:1234/v1/models).data | Select-Object id
```

5. With one model loaded, leave `LM_STUDIO_MODEL=` blank in `.env` for automatic selection; otherwise specify the exact API model ID. Start **both** processes in separate terminals:

```powershell
.\start_ui.bat
# In another terminal:
.\start_worker.bat
```

6. Open **http://127.0.0.1:7860**. Use *Model Connection* to check the loaded model.

## Switching models

Candidate names (exact published model keys and licensing must be verified with their respective publishers):

- Gemma 4 26B A4B QAT
- Qwen3.8 27B Heretic Ara 16GB VRAM XS MTP GGUF IQ4_XS

**Stop the UI and worker before switching.** You can use LM Studio's UI, or:

```powershell
powershell -ExecutionPolicy Bypass -File .\switch_model.ps1
```

Select the downloaded model by number, confirm, and restart the UI and worker. The script requests context length `2048`, but does not force GPU offload; the server's loading defaults apply. For GPU-offload tuning use LM Studio's load controls or its CLI. Check actual API IDs after loading. Switching while a task runs can fail the task.

## Architecture

```text
Gradio UI (app.py) ──────┐
                         ├── SQLite (tasks, runs, FTS5)
APScheduler (worker.py) ─┤
                         └── Agent (restricted tools) ── LM Studio localhost API ── GGUF
```

See [Architecture](docs/architecture.md), [Installation](docs/installation.md), [Configuration](docs/configuration.md), [Operations](docs/operations.md), and [Security](SECURITY.md).

## Security

`.env`, databases, user documents, logs, workspaces and model weights are ignored by Git. **`.gitignore` does not erase previously committed secrets.** Review `git ls-files`, staged changes, and commit history before publishing. API and UI are intended for `127.0.0.1` only. Uploaded documents and tool outputs are untrusted; the agent cannot run arbitrary shell commands or send data to external services with its built-in tools.

## Limitations

- Model-specific tool calling and VRAM usage have **not** been validated on every candidate GGUF.
- Japanese tokenization in SQLite FTS5 is limited; this is keyword search, not semantic retrieval.
- Background tasks require the worker process to remain running; PC sleep/shutdown pauses execution. No catch-up guarantee after downtime.
- Do not run multiple worker instances against the same DB.
- Scheduled tasks are autonomous only within registered prompts and allowlisted tools.

## Tests

```powershell
python -m pip install pytest
python -m pytest -q
```

CI runs offline syntax and unit tests; it does **not** run LM Studio inference.

## License

MIT for this project's source code. **Model weights and third-party packages retain their own licenses.** Verify model redistribution and usage terms with their publishers.

## Dashboard appearance / troubleshooting

The dashboard uses scoped CSS in `ui/custom.css` and a responsive three-column HTML grid in `app.py`.
The status cards describe components, **not** live connection health; use **Model Connection → Check Connection** for actual status.
If text appears dark on dark backgrounds or cards stack on desktop, update both files, restart `start_ui.bat`, and hard-refresh the browser (`Ctrl+F5`).
On a narrow window (under 720px), the cards intentionally stack.

## UIからモデルを切り替える / Switch models

`Model Connection` タブで「モデル一覧を更新」→モデル選択→確認チェック→切り替えを実行できます。切り替え中はワーカーを停止してください。詳細は [モデル切り替え手順](docs/model-switching.md) を参照してください。
