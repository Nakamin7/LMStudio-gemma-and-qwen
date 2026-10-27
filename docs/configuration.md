# Configuration

Copy `.env.example` to `.env`. Restart the UI and worker after changing the environment file.

| Variable | Purpose |
| --- | --- |
| `LM_STUDIO_BASE_URL` | Local OpenAI-compatible endpoint (default `http://127.0.0.1:1234/v1`) |
| `LM_STUDIO_MODEL` | Optional fallback loaded instance ID; normally leave empty |
| `LM_STUDIO_API_KEY` | Local LM Studio authentication key or placeholder `lm-studio` |
| `OPENAI_API_KEY` | OpenAI Platform API key, used only when the OpenAI provider is selected |
| `GEMINI_API_KEY` | Gemini API key, used only when the Gemini provider is selected |
| `AGENT_MAX_STEPS` | Maximum model/tool rounds per agent request (bounded 1–10) |
| `AGENT_TIMEOUT_SECONDS` | Model request timeout in seconds |

The provider and cloud model ID are stored in `provider_selection.sqlite3`. The selected local LM Studio instance ID is stored separately in `model_selection.sqlite3`. Both files are ignored by Git. Credentials are **never** stored in these SQLite databases.

Model selection occurs in **Model Connection**, and new chat/scheduled requests read the selected provider when they begin. The project does **not** automatically fall back to a cloud provider when LM Studio is unavailable.

See [Cloud Provider Guide](cloud-providers.md) for data-transfer and billing considerations.
