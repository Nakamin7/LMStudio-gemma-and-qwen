# Architecture

The Gradio UI (`app.py`) and APScheduler worker (`worker.py`) share SQLite state. The agent resolves the selected inference provider **at the start of each request** via `src/providers.py`.

```text
Gradio UI / worker.py
        │
        ├── SQLite: tasks, run history, document FTS5
        └── src/agent.py
               │
               └── src/providers.py (SQLite provider preference)
                     ├── LM Studio  http://127.0.0.1:1234/v1
                     ├── OpenAI     https://api.openai.com/v1
                     └── Gemini     https://generativelanguage.googleapis.com/v1beta/openai/
                               │
                           Allowlisted tools
```

Providers use the OpenAI Python client, since LM Studio and Gemini expose compatible endpoints for Chat Completions. A supported chat model must implement tool calling for agent tools to work. No provider API key is stored in SQLite.

## Trust boundaries

- LM Studio inference stays local; OpenAI and Gemini inference transmits request data to external services.
- Cloud tool calls can cause retrieved document snippets or workspace text to be sent to a remote model.
- The UI binds to `127.0.0.1`; it has no public authentication controls.
- Arbitrary shell commands, web-browser automation, X monitoring, and unrestricted filesystem access are not included.
- SQLite stores task prompts and results, local document chunks, and selected model IDs.
- Models, documents, and tool outputs are untrusted content; prompt injection risks still exist.
