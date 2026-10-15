# Model Switching Guide

This guide explains how to switch between locally downloaded Large Language Models (LLMs) using the LM Studio Agent web interface.

The application supports model selection through LM Studio's local REST API, allowing users to switch between compatible models without manually editing Python source files.

## 1. Prerequisites

Before switching models, ensure that the following requirements are met:

- LM Studio is installed and running.
- The LM Studio local API server is enabled.
- The desired models have already been downloaded.
- The Gradio web interface is accessible.
- The background worker (`worker.py`) is stopped.
- No chat requests or scheduled inference tasks are running.
- Sufficient system RAM and GPU memory are available.

### Supported Model Examples

The following models are examples of the intended local deployment configuration:

- Gemma 4 26B A4B QAT
- Qwen3.8 27B Heretic Ara 16GB VRAM XS MTP GGUF IQ4_XS

Model compatibility, memory requirements, and tool-calling capabilities depend on the model file and LM Studio configuration.

## 2. Start LM Studio

1. Launch LM Studio.
2. Confirm that the desired models are available in your local model library.
3. Start the local API server.
4. Verify that the server is accessible at:

   `http://127.0.0.1:1234`

You can check the available models using PowerShell:

```powershell
Invoke-RestMethod http://127.0.0.1:1234/api/v1/models
```

The response should contain information about the models available in LM Studio.

## 3. Start the Web Interface

Open PowerShell and navigate to the project directory:

```powershell
cd C:\projects\LMStudio-gemma-and-quen
```

Start the Gradio application:

```powershell
.\start_ui.bat
```

Open the following address in your browser:

`http://127.0.0.1:7860`

## 4. Switch Models Through the Web UI

### Step 1: Stop the Background Worker

If `start_worker.bat` is running, stop it using `Ctrl + C` in its terminal window.

Wait until all active inference tasks have completed.

### Step 2: Open the Model Connection Tab

In the Gradio interface, navigate to **Model Connection**.

This section provides controls for viewing available models, selecting a model, and initiating model switching.

### Step 3: Refresh the Model List

Click **Refresh Model List**.

The application retrieves the locally available models from LM Studio.

Downloaded models may appear in the list even if they are not currently loaded into memory.

### Step 4: Select the Target Model

Choose the desired model from the dropdown menu.

For example:

- Gemma 4 26B A4B QAT
- Qwen3.8 27B Heretic Ara IQ4_XS

The displayed names depend on the model metadata returned by LM Studio.

### Step 5: Configure Context Length

Select the context length based on your available system resources.

| Context Length | Suggested Use |
|---|---|
| 1024 | Lower memory usage and initial troubleshooting |
| 2048 | Recommended initial configuration |
| 4096 | Longer conversations when sufficient memory is available |

Higher context lengths generally increase memory requirements.

### Step 6: Configure GPU KV Cache Offloading

Choose whether to enable **Offload KV Cache to GPU**.

- Enabled: Stores the KV cache on the GPU when supported, increasing VRAM usage.
- Disabled: Avoids GPU placement of the KV cache and may reduce VRAM pressure.

For systems with limited VRAM, begin with this option disabled.

### Step 7: Confirm That Inference Has Stopped

Select the confirmation checkbox indicating that:

- The background worker has been stopped.
- No inference requests are currently running.
- It is safe to unload the currently loaded model.

### Step 8: Switch to the Selected Model

Click **Switch to Selected Model**.

The application attempts to:

1. Identify the currently loaded model instances.
2. Unload the existing model instances.
3. Load the selected model using the specified settings.
4. Save the selected model information for subsequent inference requests.
5. Display the result of the switching operation.

**Warning:** If the new model fails to load, the previously loaded model may remain unloaded.

### Step 9: Verify the Model Connection

Click **Check Connection Status**.

Confirm that the selected model is available and that the application reports no connection errors.

You can also inspect the loaded model instances through PowerShell:

```powershell
$response = Invoke-RestMethod http://127.0.0.1:1234/api/v1/models

$response.models |
    Select-Object key, display_name, loaded_instances
```

### Step 10: Restart the Background Worker

After confirming that the selected model has loaded successfully, restart the background worker:

```powershell
.\start_worker.bat
```

Scheduled tasks can now resume using the configured model selection.

## 5. Troubleshooting

### 5.1 Multiple Models Are Detected

**Symptom:**

The application displays an error indicating that multiple models are loaded.

**Possible cause:**

The model detection logic may be treating all downloaded models as actively loaded models.

**Solution:**

Check the `loaded_instances` field returned by LM Studio's REST API.

A downloaded model is not necessarily loaded into memory.

If multiple model instances are actually loaded, unload unnecessary instances before switching.

### 5.2 Model Loading Fails Due to Insufficient Memory

**Symptom:**

LM Studio reports insufficient system resources or fails to load the selected model.

**Solution:**

1. Reduce the context length to 2048 or 1024.
2. Disable GPU KV cache offloading.
3. Unload other models.
4. Close applications consuming substantial GPU memory.
5. Adjust GPU offloading settings in LM Studio if necessary.
6. Retry the model loading operation.

Do not disable memory safety checks unless you understand the associated risks.

### 5.3 The Selected Model Is Not Used for Inference

**Symptom:**

The UI reports that a new model has been selected, but chat responses appear to use the previous model.

**Possible causes:**

- A fixed model ID is configured in `.env`.
- The inference client is using a cached model selection.
- The background worker has not reloaded the updated configuration.

**Solution:**

1. Check the `LM_STUDIO_MODEL` setting in `.env`.
2. Confirm that the application reads the model selection saved by the Web UI.
3. Restart the Gradio application if necessary.
4. Restart the background worker.
5. Verify the active model through LM Studio.

### 5.4 LM Studio Cannot Be Reached

**Symptom:**

The application displays a connection error.

**Solution:**

1. Confirm that LM Studio is running.
2. Verify that the local API server is enabled.
3. Check that port `1234` is available.
4. Confirm that the configured API endpoint is correct.

The default OpenAI-compatible API endpoint is:

`http://127.0.0.1:1234/v1`

### 5.5 The Switch Button Does Not Work

**Symptom:**

The interface displays a message requesting confirmation before switching.

**Solution:**

1. Stop the background worker.
2. Ensure that no inference requests are running.
3. Select the confirmation checkbox.
4. Click **Switch to Selected Model** again.

If the operation still fails, inspect the error message displayed in the switching result panel.

## 6. Security Considerations

- Keep the LM Studio API server bound to the local machine unless remote access is explicitly required and properly secured.
- Do not expose the Gradio interface publicly without authentication and access controls.
- Do not commit `.env`, local databases, private documents, or model files to GitHub.
- Stop background inference tasks before unloading models.
- Avoid running multiple large models simultaneously on memory-constrained systems.

## 7. Operational Limitations

- Model switching requires the LM Studio API server to be available.
- Switching may interrupt active inference requests.
- Model loading time depends on hardware and model size.
- GPU offloading settings may require additional configuration in LM Studio.
- Tool-calling support varies between models.
- Successful model loading does not guarantee that every agent feature will work correctly.

## 8. Related Documentation

- [README](../README.md)
- [Installation Guide](installation.md)
- [Configuration Guide](configuration.md)
- [Operations Guide](operations.md)
