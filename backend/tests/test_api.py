from fastapi.testclient import TestClient
from pytest import MonkeyPatch

import app.main as main_module
from app.main import app
from app.providers import get_ai_provider
from app.providers.fake_provider import FakeProvider
from app.schemas import AnalysisResult, Severity


def test_health() -> None:
    with TestClient(app) as client:
        response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_analyze_validates_short_input() -> None:
    with TestClient(app) as client:
        response = client.post("/api/v1/analyze", json={"text": "short"})
    assert response.status_code == 422


def test_analysis_result_schema() -> None:
    result = AnalysisResult(
        summary="Dependency mismatch",
        severity=Severity.warning,
        likely_causes=["Incompatible package versions"],
        recommended_actions=["Align dependency versions"],
    )
    assert result.severity == "warning"


def test_analyze_returns_structured_result(monkeypatch: MonkeyPatch) -> None:
    expected = AnalysisResult(
        summary="Database connection timed out",
        severity=Severity.warning,
        likely_causes=["Database is unreachable"],
        recommended_actions=["Check the database connection string"],
    )

    async def no_cache(_: str):
        return None

    async def ignore_write(*args, **kwargs):
        return None

    monkeypatch.setattr(main_module, "get_cached", no_cache)
    monkeypatch.setattr(main_module, "set_cached", ignore_write)
    monkeypatch.setattr(main_module, "save_analysis", ignore_write)

    class TestProvider:
        name = "test"
        cache_namespace = "test:v1"

        async def analyze(self, _: str):
            return expected

    app.dependency_overrides[get_ai_provider] = TestProvider

    try:
        with TestClient(app) as client:
            response = client.post(
                "/api/v1/analyze",
                json={"text": "The service repeatedly reports a database timeout."},
            )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    assert response.json() == {
        "analysis": expected.model_dump(mode="json"),
        "provider": "test",
        "cached": False,
    }


def test_fake_provider_is_deterministic() -> None:
    import asyncio

    provider = FakeProvider()
    first = asyncio.run(provider.analyze("The application had a fatal crash."))
    second = asyncio.run(provider.analyze("The application had a fatal crash."))
    assert first == second
    assert first.severity == Severity.critical
