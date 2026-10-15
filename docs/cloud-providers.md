# Cloud Provider Guide (OpenAI and Gemini)

## Scope

The project supports three inference backends: `local` (LM Studio), `openai` (OpenAI API), and `gemini` (Google Gemini API). X/Twitter monitoring is intentionally **out of scope**.

The ChatGPT website is not an API endpoint. A ChatGPT subscription does **not** pay for OpenAI API usage.

## Setup

1. In PowerShell, create `.env` from `.env.example` if needed: `Copy-Item .env.example .env`.
2. For OpenAI, get an API key at https://platform.openai.com/api-keys and put it in `OPENAI_API_KEY=` in `.env`. Enable appropriate API billing/limits in the OpenAI Platform.
3. For Gemini, get an API key at https://aistudio.google.com/apikey and put it in `GEMINI_API_KEY=` in `.env`. Check quotas and pricing for the account and selected model.
4. Stop and restart `start_ui.bat` and `start_worker.bat` after editing `.env` because environment values are loaded at process startup.
5. Open `http://127.0.0.1:7860` → **Model Connection**.
6. Select **OpenAI API** or **Google Gemini API**, click **Fetch Model List**, and choose a model ID (or enter a valid model ID manually).
7. Check the cloud transmission/billing acknowledgment and click **Save Inference Target**.
8. Verify the active provider in the status box; test a small prompt in **AI Chat**.

The UI interface may present action labels in Japanese (for example, **モデル一覧を取得** and **この推論先を保存**).

## Model IDs

Model IDs are retrieved from each provider's API; no fixed list is assumed. Examples of previously published IDs include `gpt-4.1-mini` and `gemini-2.5-flash`. Availability depends on the user's account, model lifecycle, API access, and selected endpoint. Not every returned ID supports Chat Completions or function calling. Start with a model known to support both.

## Code architecture

- `src/providers.py`: API client factory, model listing, persisted provider selection, and inference routing.
- `src/agent.py`: calls `resolve_inference()` at the start of every chat or scheduled task, retaining restricted tools.
- `app.py`: provider dropdown, model dropdown, save button, consent checkbox, and status display.
- `src/scheduler.py`: existing worker uses `agent.ask()`; no new scheduler is needed.
- `provider_selection.sqlite3`: local, ignored SQLite store with provider and cloud model IDs. **No API key is stored in SQLite.**
- `model_selection.sqlite3`: local, ignored SQLite store for the selected LM Studio instance.

## Privacy, cost, and security

Cloud requests transmit the system prompt, the user's current prompt, recent chat history, and **any allowlisted tool output the cloud model requests**. In particular, `search_knowledge_base` may include excerpts from locally uploaded documents, and `read_workspace_file` may include local file text. Do not use the cloud provider with confidential documents unless that transfer is permitted.

- API keys remain in `.env` only. Never paste them into the browser UI, logs, commits, or chat prompts.
- The provider choice is deliberate: the app does **not** silently fail over from local to cloud or cloud to another cloud API.
- Model list retrieval authenticates with the provider but does not guarantee that inference will succeed.
- Cloud inference can incur token-based charges. Turning on a scheduled task while a cloud provider is selected can incur **repeated unattended charges**. Pause scheduled tasks as needed and configure spending limits at the provider.
- Model responses may request tool execution; only the existing allowlisted tools are available.
- Switching an active provider does not abort a request already in progress. Restart the worker if the `.env` keys were changed.

## Troubleshooting

- **Missing API key**: check `OPENAI_API_KEY` or `GEMINI_API_KEY` in `.env`; restart the UI/worker.
- **401/403**: the key, project, billing, or access rights may be incorrect.
- **429**: provider quota or rate limit exceeded.
- **Unsupported model or tools**: choose a model that supports Chat Completions and function calling, or change the integration for models that require other APIs.
- **Unexpected model**: check **Current Inference Target** and press **Save Inference Target** after changing the dropdowns.
- **No local model**: start LM Studio, load an LLM, and select `LM Studio (local)`.
- **Costs after switching**: the worker uses the selected provider for *each new task execution*. Pause tasks when not needed.

## API references

- OpenAI Chat Completions: https://platform.openai.com/docs/api-reference/chat/create
- Google Gemini OpenAI compatibility: https://ai.google.dev/gemini-api/docs/openai

## Gemini model-list troubleshooting

The model dropdown reads Google’s native `GET /v1beta/models` catalog using the `x-goog-api-key` header, follows pagination, and only shows `gemini-*` models advertising `generateContent`. HTTP errors include the Google status/message and the key is never placed in the URL. This avoids depending on the OpenAI-compatible `/models` listing for discovery. It does not guarantee every listed model supports OpenAI-style Chat Completions or tool calling; test the selected model with the agent.

If the list is empty or the request fails, check the displayed HTTP status and Google API error message, confirm the key belongs to a Google AI Studio project with Gemini API access, and check project/API restrictions and quota. Never share `.env` or commit API keys. If a key has been exposed, revoke it and create a replacement.
