# Operations & troubleshooting

## Start/stop

- `start_ui.bat`: Gradio interface at `http://127.0.0.1:7860`.
- `start_worker.bat`: APScheduler task worker.
- Stop each process with Ctrl+C. Keep the worker running for scheduled tasks.
- Avoid running multiple workers concurrently.

## Model loading errors

If LM Studio reports insufficient resources, unload other models, reduce context length, reduce GPU offload, and close GPU-heavy applications. Do not bypass model-loading safety guardrails as a first resort.

## Missing `lms` command

Use LM Studio's GUI or the provided REST API script once the server is running. The CLI must be installed/available in PATH to use `lms` commands.

## Tool calling fails

Some GGUF models or templates do not support OpenAI-compatible tool calls reliably. Verify with a simple calculator prompt, and check the model card.

## Document search

SQLite FTS5 uses lexical matching; Japanese without spaces may return weak results. Vector embeddings are not included.
