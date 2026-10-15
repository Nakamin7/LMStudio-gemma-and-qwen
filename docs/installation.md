# Installation (Windows)

1. Install Python 3.11 and LM Studio.
2. Clone the repository and run `py -3.11 -m venv .venv`.
3. Activate `.venv\Scripts\Activate.ps1`, then run `python -m pip install -r requirements.txt`.
4. Run `Copy-Item .env.example .env`. Do not commit `.env`.
5. Load one model in LM Studio and start its local API server.
6. Check `http://127.0.0.1:1234/v1/models` for the exact model ID.
7. Start `start_ui.bat` and `start_worker.bat` separately.
8. Open `http://127.0.0.1:7860`.

On a 16 GB VRAM system, start with context length 2048 and a conservative GPU offload. Model loading can fail due to combined GPU/system memory requirements.
