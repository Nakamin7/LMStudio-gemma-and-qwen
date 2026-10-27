# Switch Models Using the Web UI

This guide covers both provider selection and LM Studio local model loading.

## A. Switch inference provider (LM Studio / OpenAI / Gemini)

1. Start the Gradio web UI with `start_ui.bat`, then open `http://127.0.0.1:7860`.
2. Select the **Model Connection** tab.
3. Choose **LM Studio (local)**, **OpenAI API**, or **Google Gemini API**.
4. For a cloud API, configure its API key in `.env` and restart the UI first.
5. For a cloud API, click **Fetch Model List** and choose a compatible model ID. The model list does not guarantee support for Chat Completions or tool calling.
6. Check the cloud-data transmission and possible billing acknowledgment when selecting a cloud provider.
7. Click **Save Inference Target**, then verify **Current Inference Target**. Merely changing dropdown values does not persist the selection.
8. Test a small request using the **AI Chat** tab. Subsequent scheduled tasks use the newly selected provider too.

**Privacy:** Cloud requests may include the system prompt, chat messages, recent history, and local document or workspace excerpts returned by enabled tools. **Costs:** Cloud API billing is separate from a ChatGPT subscription and may apply to recurring scheduled tasks.

## B. Switch between local LM Studio models

1. Start LM Studio and its local API server. Download the desired GGUF model in LM Studio.
2. Stop `start_worker.bat` and wait for running chat requests to finish.
3. Open **Model Connection** and scroll to the local model section.
4. Click **Refresh Model List** for LM Studio; choose a downloaded model.
5. Start with context length `2048`; disable GPU KV cache placement if VRAM is constrained.
6. Confirm that the worker is stopped and no inference is running, then click **Switch to Selected Model**.
7. Verify the result and set **LM Studio (local)** as the inference provider using **Save Inference Target**.
8. Restart the worker if needed.

The local switch uses LM Studio's native `/api/v1/models`, `/api/v1/models/unload`, and `/api/v1/models/load` endpoints. Unloading the previous model can leave no model loaded if loading the new one fails. Local selection is stored in `model_selection.sqlite3`. Cloud model and provider selection is stored in `provider_selection.sqlite3`; API keys are not stored in either database.

## Troubleshooting

- **Multiple models listed:** downloaded models are not necessarily loaded. Check `loaded_instances` using `GET /api/v1/models`.
- **Memory error:** reduce context length, unload other models, and adjust LM Studio offloading settings.
- **Cloud API error:** verify the API key, account/API permissions, model's Chat Completions capabilities, provider quota, and billing status.
- **Cloud model used during scheduled tasks:** the worker reads the active provider for each new task. Disable tasks or return to LM Studio when cloud use is not intended.
- **Cannot connect to LM Studio:** ensure its local server is running at `http://127.0.0.1:1234`.

See [Cloud Provider Guide](cloud-providers.md), [Configuration](configuration.md), and [Operations](operations.md).
