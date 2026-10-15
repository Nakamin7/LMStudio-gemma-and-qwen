# Security Policy

This experimental agent is for local trusted use. The Gradio UI binds to `127.0.0.1` and has no multi-user authentication; never publicly expose it as-is.

## Cloud inference

Selecting OpenAI or Gemini transmits chat requests and context to external cloud APIs. Responses to allowlisted tools can include text from local indexed documents or files in `workspace/`; these **can be uploaded as part of the next model request**. Do not enable cloud inference when local confidential content may be exposed without permission. The UI requests user acknowledgment before activating cloud APIs.

- Keep `OPENAI_API_KEY` and `GEMINI_API_KEY` in your local `.env`, not in chat/UI/commits.
- `provider_selection.sqlite3` contains only provider/model IDs; API secrets are not persisted there.
- Cloud costs and rate limits apply, including scheduled tasks. Configure spending limits at the API provider.
- Never run arbitrary shell commands suggested by model outputs. Existing tools are explicitly allowlisted.
- No X/Twitter integration is included in this release.

## Publishing

Review `git status`, `git diff --cached`, `git ls-files`, and commit history to ensure that no `.env`, database, logs, user documents, or model weights have ever been committed. `.gitignore` does not remove secrets from existing Git history.

## Reports

Do not send API keys, access tokens, local private documents, or logs containing secrets when reporting issues.
