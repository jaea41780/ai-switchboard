from app.config import Settings, get_settings
from app.providers.base import AIProvider
from app.providers.fake_provider import FakeProvider
from app.providers.ollama_provider import OllamaProvider
from app.providers.openai_provider import OpenAIProvider


def create_provider(settings: Settings) -> AIProvider:
    if settings.ai_provider == "openai":
        return OpenAIProvider(
            api_key=settings.openai_api_key,
            model=settings.openai_model,
        )
    if settings.ai_provider == "fake":
        return FakeProvider()
    if settings.ai_provider == "ollama":
        return OllamaProvider(
            base_url=settings.ollama_base_url,
            model=settings.ollama_model,
            timeout_seconds=settings.ollama_timeout_seconds,
        )
    raise ValueError(f"Unsupported AI provider: {settings.ai_provider}")


def get_ai_provider() -> AIProvider:
    return create_provider(get_settings())


def get_ai_providers() -> list[AIProvider]:
    """Providers used by the multi-AI endpoint.

    Use the selected provider. Local Ollama is the default, so multi-analysis
    remains usable without API credentials or a hosted model subscription.
    """
    settings = get_settings()
    return [create_provider(settings)]
