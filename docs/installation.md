# Installation (Windows)

1. Install Python 3.11. LM Studio is required only for local inference.
2. Run from the project directory in PowerShell:

```powershell
py -3.11 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements-dev.txt
Copy-Item .env.example .env
```

3. For local inference, start LM Studio's server at `http://127.0.0.1:1234` and load one LLM.
4. For OpenAI or Gemini, add your corresponding API key to `.env`, then restart the UI/worker.
5. Start `.\start_ui.bat`, and start `.\start_worker.bat` in a separate terminal if scheduled tasks are needed.
6. Open `http://127.0.0.1:7860` → **Model Connection** and choose your provider.

See [Cloud Provider Guide](cloud-providers.md) for API key setup, privacy, and billing implications.

## Development checks: mypy, pre-commit, and Gitleaks

From the project root, after activating the virtual environment:

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements-dev.txt
.\.venv\Scripts\python.exe -m mypy --config-file mypy.ini
.\.venv\Scripts\python.exe -m pytest -q
.\.venv\Scripts\python.exe -m pre_commit install
.\.venv\Scripts\python.exe -m pre_commit run --all-files
```

The pre-commit configuration runs Gitleaks on staged changes and mypy on the configured Python application files. Install hooks separately in each clone. CI also runs a static type check. If a check fails, fix the issue rather than bypassing the hook. Never put real API keys in test fixtures; use fake placeholder strings.
