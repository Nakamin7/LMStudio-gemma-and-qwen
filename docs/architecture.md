# Architecture

The UI (`app.py`) and scheduler worker (`worker.py`) are separate processes. Both use a local SQLite database; the worker polls for task changes every 30 seconds. The agent calls LM Studio's local OpenAI-compatible endpoint, using only allowlisted tools: arithmetic, listing/reading selected workspace text files, and SQLite FTS5 document lookup. No unrestricted OS command execution is exposed. The scheduler executes user-registered prompts at intervals; it is not a continuously reasoning agent.

## Trust boundaries

- LM Studio inference runs locally; the API is expected on `127.0.0.1`.
- Documents and tool outputs are untrusted; prompt injection is possible.
- SQLite records task prompts, document chunks, and execution results: treat the DB as private.
- UI has no authentication; bind to localhost only.
