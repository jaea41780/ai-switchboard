# AI Switchboard

**여러 AI 제공자를 한곳에서 호출하고, 구조화된 결과를 하나의 검토 가능한 실행 계획으로 정리하는 초기 실험 프로젝트입니다.**

An early experiment for calling multiple AI providers, combining structured results, and turning a conclusion into a reviewable action plan.

> **Project status:** early prototype. The website is an interactive simulation. Its model selectors (GPT-6 Astra/Sol/Luna, Claude, and internal models) do not call those models. The backend currently has an OpenAI adapter and a local fake provider; Claude and other providers need adapters and credentials before they can be used.

## Demo

The current hosted demo is account-restricted. Public access has not been enabled yet.

GitHub Pages can publish the simulation from the web/ directory after Pages is enabled in repository settings. The included workflow is manual so the demo is not published until you start that deployment.

## What it demonstrates

- A shared AIProvider contract and provider factory
- A multi-provider endpoint at POST /api/v1/analyze/multi
- Concurrent provider calls with failure isolation
- A normalized Pydantic response and deterministic consensus
- FastAPI, PostgreSQL, and Redis integration
- A computer-action plan that requires approval and an allowlisted operation
- A multilingual static web simulation

Computer control is disabled by default. The current macOS controller only supports showing a notification and opening allowlisted apps or HTTP(S) URLs. It does not provide general mouse, keyboard, or screen control.

## Quick start

Requirements: Python 3.11+ and Docker Desktop.

    cd backend
    cp .env.example .env
    # Add your own OpenAI API key to OPENAI_API_KEY in .env to use OpenAI.
    docker compose up --build

The API documentation is at http://localhost:8000/docs.

## API examples

Single-provider analysis:

    curl -X POST http://localhost:8000/api/v1/analyze -H 'Content-Type: application/json' -d '{"text":"The service repeatedly reports a database connection timeout."}'

Multi-provider analysis:

    curl -X POST http://localhost:8000/api/v1/analyze/multi -H 'Content-Type: application/json' -d '{"text":"The service repeatedly reports a database connection timeout."}'

The multi-provider response includes each provider's result, any provider-specific error, and a consensus result. Configure OPENAI_API_KEY to enable the OpenAI adapter; otherwise the local fake provider is used.

## Computer action flow

1. POST /api/v1/actions/plan converts a structured conclusion into a small action plan.
2. The client shows the plan and obtains explicit user approval.
3. POST /api/v1/actions/execute checks approval, the feature flag, and the app allowlist before running an action.

Computer control is off unless ENABLE_COMPUTER_CONTROL=true is set on the local macOS machine. Keep it disabled when running in a public or shared environment.

## Tests

    cd backend
    python -m pip install -r requirements.txt
    PYTHONPATH=. python -m pytest -q

GitHub Actions runs the test suite on pushes and pull requests.

## Add a provider

Implement the AIProvider contract in backend/app/providers/, then register it in backend/app/providers/factory.py. Each adapter should return the same AnalysisResult schema. Keep credentials in environment variables and never commit .env.

## Security

- Never commit API keys, .env, personal data, or production credentials.
- The browser demo makes no AI API calls and sends no prompt to a provider.
- Computer control is disabled by default and checks explicit approval plus an allowlist.
- Treat model output as untrusted input; validate every proposed action before execution.
- Report vulnerabilities privately using GitHub's Security tab.

## Contributing

Issues and pull requests are welcome. Please describe the problem, expected behavior, and how you tested the change. See CONTRIBUTING.md.

## License

No reuse license has been selected yet. Choose a license before presenting this repository as open source.
