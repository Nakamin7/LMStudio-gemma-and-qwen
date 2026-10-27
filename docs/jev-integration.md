# Jev integration: privacy, consent, and permissions

## Purpose

Jev is used only as an optional relevance judge for local Knowledge Base search results. It is not a chat provider and is not given any application tools. The existing LM Studio/OpenAI/Gemini chat flow is unchanged.

## Data sent

Only when both `Jevの関連度判定を有効にする` and the separate Jev disclosure/consent checkbox are saved as enabled, the app sends up to four retrieved passages to `https://api.typesafe.ai/v1/systemone`:

- the current search query (at most 2,000 characters)
- candidate source filename (at most 160 characters)
- candidate passage excerpt (at most 1,200 characters)
- the fixed relevance-judgment instruction and model ID

No API key other than the Jev bearer key is included in the request body. The Jev key is read server-side from `TYPESAFE_API_KEY` and must never be committed. Do not enable Jev for sensitive/private documents unless sending those excerpts to the external provider is approved. Review the current TypeSafe AI terms, privacy information, pricing, retention and limits before use.

## Consent behavior

- Jev is off by default.
- Enabling Jev without the explicit Jev consent checkbox is rejected.
- Jev consent is independent of OpenAI/Gemini provider consent.
- Turning Jev off prevents subsequent calls; the saved consent can be unchecked to revoke it.
- If Jev is unavailable or returns an invalid response, the app falls back to local search results.

## Permission boundary

Jev receives only strings describing a question and candidate passage. It does not receive the `FUNCTIONS` or `SCHEMAS` tool definitions, API clients, credentials, file paths for direct access, or permission to read/delete files or change settings. Its output only influences relevance filtering. It must never authorize destructive actions. Actual tool execution remains in `src/agent.py` / `src/tools.py` and their explicit allowlist.

## Setup (PowerShell)

1. Create a key through the official TypeSafe AI console/docs and review the current terms, privacy notice, price, and limits.
2. Put the key in `.env` (which is gitignored):

   ```dotenv
   TYPESAFE_API_KEY=your_real_key_here
   JEV_MODEL=jev-1.13.0
   JEV_RELEVANCE_THRESHOLD=0.80
   ```

3. Restart the app. Jev remains off until enabled in Model Connection and the Jev-specific disclosure is accepted.
4. Test offline with `python -m pytest tests/test_jev.py -q`. This uses mocks and does not make a paid API request.

## Limitations

- The threshold is a tuning parameter, not a guarantee of correctness.
- Search is currently local SQLite FTS5 lexical search; Jev only re-ranks/filters its first four results.
- If Jev rejects every result, the local results are returned with a fallback notice to avoid falsely claiming there is no evidence.
- This feature does not fix Gemini HTTP 503 or Gemini `thought_signature` HTTP 400 errors.
