# Configuration

All local settings belong in `.env` (copied from `.env.example`).

| Variable | Purpose |
| --- | --- |
| `LM_STUDIO_BASE_URL` | Local OpenAI-compatible endpoint, usually `http://127.0.0.1:1234/v1` |
| `LM_STUDIO_MODEL` | Exact model ID; leave blank to auto-select the **single loaded** model |
| `LM_STUDIO_API_KEY` | Placeholder `lm-studio` for local no-auth API; replace if API authentication is configured |
| `AGENT_MAX_STEPS` | Maximum tool-call rounds |
| `AGENT_TIMEOUT_SECONDS` | LLM request timeout |

The REST model-switch script uses LM Studio's native `/api/v1/models` API. Stop both processes before switching.

The project does not download model weights. Exact model names, compatibility and licenses must be verified against the source model cards.
