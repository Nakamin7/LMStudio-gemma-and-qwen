# OpenAI Responses API migration

## Summary

The agent uses the Responses API only when the selected provider is `openai`. Gemini's OpenAI-compatible endpoint and LM Studio keep their current Chat Completions request path. This is intentional: API compatibility differs by provider, and moving all providers at once would risk reintroducing Gemini tool-call/signature issues or breaking local inference.

## What changed

- `src/agent.py`: OpenAI requests now call `api.responses.create()`. The agent reads function calls from `response.output`, executes only functions registered in `src.tools.FUNCTIONS`, and sends each result as a `function_call_output` item with the exact `call_id` returned by the model.
- The agent replays every output item from a response into the next request's input, including reasoning and function-call items. Do not filter out reasoning items; doing so can invalidate the model's next turn.
- `src/agent.py`: the Chat Completions path remains for Gemini and LM Studio. The existing Chat Completions schemas remain the canonical schema source and are converted to Responses function definitions at runtime.
- `requirements.txt`: the minimum OpenAI Python SDK version is raised to 1.66 to ensure the Responses resource is available.
- `tests/test_responses_agent.py`: tests cover tool schema conversion, `call_id` linkage, text-only answers, Gemini routing, and incomplete API responses.

## Data retention and reasoning continuity

OpenAI calls pass `store=False` and request `reasoning.encrypted_content`. This avoids requesting server-side response storage while retaining encrypted reasoning items needed for stateless tool turns. The application still sends the prompt, recent chat history, and any tool results requested by the model to OpenAI. `store=False` does not mean the API request is not processed by the provider.

## Impact

### Expected to change

- Only OpenAI inference uses `/v1/responses` and Responses-style tool declarations/output items.
- OpenAI model compatibility changes: the selected model and account/API endpoint must support Responses API and function calling.
- OpenAI tool-call context is handled as Responses items rather than Chat Completions messages.
- The minimum `openai` dependency version increases.

### Intended to remain unchanged

- Public `ask(question, history)` interface used by `app.py` and the worker.
- The names, permissions, and internal execution logic of approved tools in `src/tools.py`.
- GraphRAG, FTS5/vector retrieval, evidence citation checks, database schemas, Gradio UI, scheduled task configuration, and provider-selection database.
- Gemini and LM Studio stay on Chat Completions.

### Limitations

- This is not a guarantee that every OpenAI-compatible proxy or every model alias implements `/v1/responses`. If using a proxy/base URL rather than the official OpenAI endpoint, verify it supports Responses API input/output items and `store`/`include` parameters.
- Tests are mocked; a live API call is required to verify the actual model/account.
- `strict=False` is deliberately used so existing JSON schemas are not forced into strict-schema requirements during migration.

## Install and validate on Windows

```powershell
.\.venv\Scripts\python.exe -m pip install --upgrade -r requirements-dev.txt
.\.venv\Scripts\python.exe -m compileall -q src app.py worker.py evaluation tests
.\.venv\Scripts\python.exe -m pytest -q
.\.venv\Scripts\python.exe -m mypy --config-file mypy.ini
.\.venv\Scripts\python.exe -m pre_commit run --all-files
```

Then select OpenAI and the model in **Model Connection** and test, in order:

1. A text-only question that needs no tool.
2. A calculation request to exercise function calling.
3. A knowledge-base question to test retrieval and citation tracking.

Then switch to Gemini and LM Studio and verify each still uses its Chat Completions endpoint.
