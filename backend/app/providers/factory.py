from app.config import Settings, get_settings
from app.providers.base import AIProvider
from app.providers.fake_provider import FakeProvider
from app.providers.openai_provider import OpenAIProvider


def create_provider(settings: Settings) -> AIProvider:
    if settings.ai_provider == "openai":
        return OpenAIProvider(
            api_key=settings.openai_api_key,
            model=settings.openai_model,
        )
    if settings.ai_provider == "fake":
        return FakeProvider()
    raise ValueError(f"Unsupported AI provider: {settings.ai_provider}")


def get_ai_provider() -> AIProvider:
    return create_provider(get_settings())


def get_ai_providers() -> list[AIProvider]:
    """Providers used by the multi-AI endpoint.

    Add Claude, Gemini, or an internal provider here after implementing the
    shared AIProvider contract. The local provider keeps development usable
    without credentials.
    """
    settings = get_settings()
    providers: list[AIProvider] = [FakeProvider()]
    if settings.openai_api_key:
        providers.insert(0, create_provider(settings))
    return providers
