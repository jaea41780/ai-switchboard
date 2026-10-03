import asyncio
from types import SimpleNamespace

from app.config import Settings
from app.providers.factory import create_provider
from app.providers.fake_provider import FakeProvider
from app.providers.ollama_provider import OllamaProvider
from app.providers.openai_provider import OpenAIProvider
from app.schemas import AnalysisResult, Severity


def test_factory_selects_fake_provider() -> None:
    provider = create_provider(Settings(ai_provider="fake"))
    assert isinstance(provider, FakeProvider)
    assert provider.name == "fake"


def test_factory_selects_openai_provider() -> None:
    provider = create_provider(
        Settings(
            ai_provider="openai",
            openai_api_key="test-key",
            openai_model="test-model",
        )
    )
    assert isinstance(provider, OpenAIProvider)
    assert provider.cache_namespace == "openai:test-model"


def test_factory_selects_local_ollama_provider() -> None:
    provider = create_provider(
        Settings(
            ai_provider="ollama",
            ollama_base_url="http://localhost:11434",
            ollama_model="local-test-model",
        )
    )
    assert isinstance(provider, OllamaProvider)
    assert provider.name == "ollama (local-test-model)"
    assert provider.cache_namespace == "ollama:local-test-model"


def test_openai_provider_uses_shared_result_schema() -> None:
    expected = AnalysisResult(
        summary="A dependency failed",
        severity=Severity.warning,
        likely_causes=["Version mismatch"],
        recommended_actions=["Align versions"],
    )

    class FakeResponses:
        async def parse(self, **kwargs):
            assert kwargs["text_format"] is AnalysisResult
            assert kwargs["model"] == "test-model"
            return SimpleNamespace(output_parsed=expected)

    fake_client = SimpleNamespace(responses=FakeResponses())
    provider = OpenAIProvider("", "test-model", client=fake_client)
    result = asyncio.run(provider.analyze("Some sufficiently long error log"))
    assert result == expected


def test_ollama_provider_validates_structured_result() -> None:
    expected = AnalysisResult(
        summary="Database is unavailable",
        severity=Severity.warning,
        likely_causes=["Connection timeout"],
        recommended_actions=["Check database reachability"],
    )

    class FakeHttpResponse:
        def raise_for_status(self):
            pass

        def json(self):
            return {"message": {"content": expected.model_dump_json()}}

    class FakeHttpClient:
        async def post(self, url, json):
            assert url == "http://localhost:11434/api/chat"
            assert json["model"] == "local-test-model"
            assert json["format"] == AnalysisResult.model_json_schema()
            assert json["stream"] is False
            return FakeHttpResponse()

    provider = OllamaProvider(
        "http://localhost:11434", "local-test-model", client=FakeHttpClient()
    )
    result = asyncio.run(provider.analyze("The service timed out reaching database"))
    assert result == expected


def test_providers_share_the_same_contract() -> None:
    fake = FakeProvider()
    openai = OpenAIProvider("key", "model")
    ollama = OllamaProvider("http://localhost:11434", "model")
    for provider in (fake, openai, ollama):
        assert isinstance(provider.name, str)
        assert isinstance(provider.cache_namespace, str)
        assert callable(provider.analyze)
