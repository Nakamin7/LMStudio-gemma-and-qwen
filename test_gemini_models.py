"""Standalone diagnostic for Gemini model listing. Never prints the API key."""
import os
import sys

from config import ROOT  # loads .env
from src.providers import list_provider_models

try:
    models = list_provider_models("gemini")
except Exception as exc:
    print(f"FAILED: {type(exc).__name__}: {exc}")
    sys.exit(1)

print(f"OK: {len(models)} Gemini models support generateContent")
for model in models:
    print(model)
