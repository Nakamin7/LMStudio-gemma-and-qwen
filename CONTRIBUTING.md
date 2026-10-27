# Contributing

Open an issue before substantial changes. Keep additions local-first and avoid expanding tool privileges without explicit user approval. Do not include local databases, model weights, credentials, or private documents in pull requests. Run `python -m pytest -q` before submitting.
<<<<<<< HEAD

## Secret scanning before every commit

This repository uses **pre-commit + Gitleaks** to reject staged changes that contain API keys or other secrets. Install the hook in each local clone:

```powershell
py -m pip install pre-commit
pre-commit install
```

Run the scan manually before opening a pull request:

```powershell
pre-commit run --all-files
```

To verify that the hook blocks a commit, create a temporary test file containing a clearly fake, key-shaped value, stage it, and run `pre-commit run gitleaks --all-files` (or attempt a commit). Remove the test file and unstage it afterward. **Never test with a real key.** The `.gitleaks.toml` file adds checks for common provider/API-key variable names while retaining Gitleaks' built-in rules. The GitHub Actions workflow also scans pushes and pull requests, as a second line of defense.

If a real key is detected, do not bypass the hook. Remove the secret from the staged content and rotate/revoke the exposed key if it was ever committed or shared. A pre-commit hook only protects commits made in clones where it is installed; it does not clean secrets from existing Git history.
=======
>>>>>>> d113ef0042cbe2e6b1958bac71985936af2426c0
