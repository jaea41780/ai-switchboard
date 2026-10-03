import asyncio
from types import SimpleNamespace

from app.config import Settings
from app.providers.factory import create_provider
from app.providers.fake_provider import FakeProvider
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


def test_providers_share_the_same_contract() -> None:
    fake = FakeProvider()
    openai = OpenAIProvider("key", "model")
    for provider in (fake, openai):
        assert isinstance(provider.name, str)
        assert isinstance(provider.cache_namespace, str)
        assert callable(provider.analyze)
