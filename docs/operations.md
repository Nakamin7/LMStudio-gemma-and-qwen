# Operations and Troubleshooting

- Start Gradio UI using `start_ui.bat` and the scheduler worker using `start_worker.bat`.
- Stop each process with `Ctrl+C`. Avoid running multiple scheduler workers.
- **Switch active provider:** Use **Model Connection**, fetch available model IDs for cloud APIs, and **save** the selection. The next chat or scheduled task reads it.
- **Switch local LM Studio models:** stop the worker and active inference; perform local unload/load from the UI; restart the worker.
- **Changing API keys:** edit `.env` and restart both UI and worker processes.
- **Model not found / unsupported tools:** confirm that the model supports Chat Completions with function calling.
- **Cloud API 401 / 403 / 429:** check API key, project/billing entitlement, and usage limits.
- **LM Studio memory error:** unload other models, reduce context length or GPU offload; do not bypass memory safeguards.
- **Missing `lms`:** use LM Studio GUI or the native local REST API switch UI.
- **Scheduled costs:** when a cloud provider is selected, scheduled tasks can automatically incur API usage charges. Pause tasks when not needed.
- **Document search:** SQLite FTS5 is lexical matching; Japanese without spaces may give weak results.

See [Cloud Provider Guide](cloud-providers.md).
