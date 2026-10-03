from __future__ import annotations

from typing import Any

from openai import AsyncOpenAI

from app.schemas import AnalysisResult


SYSTEM_PROMPT = """You analyze technical logs and unstructured problem reports.
Return a concise diagnosis, severity, likely causes, and safe concrete actions.
Do not invent evidence that is absent from the supplied text.
Write the result in the same language as the supplied text."""


class OpenAIProvider:
    def __init__(self, api_key: str, model: str, client: Any | None = None) -> None:
        self._api_key = api_key
        self._model = model
        self._client = client

    @property
    def name(self) -> str:
        return "openai"

    @property
    def cache_namespace(self) -> str:
        return f"{self.name}:{self._model}"

    async def analyze(self, text: str) -> AnalysisResult:
        if self._client is None:
            if not self._api_key:
                raise RuntimeError("OPENAI_API_KEY is not configured")
            self._client = AsyncOpenAI(api_key=self._api_key)

        response = await self._client.responses.parse(
            model=self._model,
            input=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": text},
            ],
            text_format=AnalysisResult,
        )
        if response.output_parsed is None:
            raise RuntimeError("The model returned no structured result")
        return response.output_parsed
