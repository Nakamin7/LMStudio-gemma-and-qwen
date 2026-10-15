# Security policy

## Intended deployment

This is a **local-only, single-user experimental project**. Gradio and LM Studio should listen only on loopback interfaces. It has no authentication, remote authorization, sandboxing, or hardened multi-tenant isolation. Do not expose it directly to the internet.

## Private files

Never commit `.env`, SQLite files (including WAL/SHM), `workspace/`, `data/documents/`, `logs/`, model weights, credentials, or unredacted screenshots. A `.gitignore` only prevents new untracked files from being added; it does not remove files already in Git history.

## Prompt injection and tool access

Documents and tool responses can contain adversarial instructions. Only restricted tools are available; avoid adding arbitrary shell execution or network exfiltration tools. Treat model output as untrusted and verify any proposed real-world actions.

## Reporting

Please report security concerns privately to the repository maintainer through GitHub's private vulnerability reporting if enabled. Do not post secrets in public issues.
