# Contributing

Thanks for helping improve AI Switchboard.

## Before opening an issue

- Search existing issues for duplicates.
- Include steps to reproduce, expected behavior, and actual behavior.
- Do not include API keys, private logs, or personal data.

## Pull requests

- Keep changes focused and explain the user-visible effect.
- Add or update tests for backend behavior changes.
- Run PYTHONPATH=. python -m pytest -q from backend/.
- Do not add real credentials or claim simulated providers are live integrations.

## Adding an AI provider

Implement the shared provider contract, normalize results to AnalysisResult, handle provider errors, and document required environment variables. Never log secrets or send user data to a new service without clearly documenting that behavior.
