from __future__ import annotations

import asyncio

from fastapi.testclient import TestClient

from app.main import app
from app.orchestrator import MultiAIOrchestrator
from app.providers import get_ai_providers
from app.schemas import AnalysisResult, Severity


class StubProvider:
    def __init__(self, name: str, result: AnalysisResult | Exception):
        self.name = name
        self.cache_namespace = name
        self.result = result

    async def analyze(self, _: str) -> AnalysisResult:
        if isinstance(self.result, Exception):
            raise self.result
        return self.result


def result(summary: str, severity: Severity, cause: str, action: str) -> AnalysisResult:
    return AnalysisResult(
        summary=summary,
        severity=severity,
        likely_causes=[cause],
        recommended_actions=[action],
    )


def test_orchestrator_combines_results_and_isolates_failure() -> None:
    providers = [
        StubProvider("openai", result("DB timeout", Severity.warning, "Network", "Retry")),
        StubProvider("claude", result("DB unavailable", Severity.critical, "DB down", "Check DB")),
        StubProvider("internal", RuntimeError("offline")),
    ]
    items, consensus = asyncio.run(MultiAIOrchestrator(providers).analyze("long input"))

    assert [item.provider for item in items] == ["openai", "claude", "internal"]
    assert items[2].error == "offline"
    assert consensus.severity == Severity.critical
    assert consensus.likely_causes == ["Network", "DB down"]


def test_orchestrator_fails_only_when_every_provider_fails() -> None:
    providers = [StubProvider("a", RuntimeError("no")), StubProvider("b", RuntimeError("no"))]
    try:
        asyncio.run(MultiAIOrchestrator(providers).analyze("long input"))
    except RuntimeError as exc:
        assert str(exc) == "All AI providers failed"
    else:
        raise AssertionError("Expected all-provider failure")


def test_multi_endpoint_returns_provider_results_and_consensus() -> None:
    providers = [
        StubProvider("one", result("First", Severity.info, "Cause", "Action")),
        StubProvider("two", result("Second", Severity.warning, "Cause", "Escalate")),
    ]
    app.dependency_overrides[get_ai_providers] = lambda: providers
    try:
        with TestClient(app) as client:
            response = client.post(
                "/api/v1/analyze/multi",
                json={"text": "The database connection repeatedly times out."},
            )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    body = response.json()
    assert body["providers_succeeded"] == 2
    assert body["providers_failed"] == 0
    assert body["consensus"]["severity"] == "warning"
    assert body["consensus"]["likely_causes"] == ["Cause"]
