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

## Git commit protection

The repository provides `.pre-commit-config.yaml` and `.gitleaks.toml`. After cloning, install the hook with `py -m pip install pre-commit` and `pre-commit install`. Gitleaks checks staged changes and rejects detected secrets, including common API-key formats and assignments to provider-specific key variables. A GitHub Actions scan provides additional protection on pushes and pull requests.

This is defense in depth, not a guarantee that every possible secret format will be detected. Never commit real credentials. If a key is exposed, revoke/rotate it immediately; deleting it in a later commit does not remove it from Git history.
