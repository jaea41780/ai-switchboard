from __future__ import annotations

from typing import Any

import httpx

from app.providers.openai_provider import SYSTEM_PROMPT
from app.schemas import AnalysisResult


class OllamaProvider:
    """Calls a model served locally by Ollama; no hosted API key is needed."""

    def __init__(
        self,
        base_url: str,
        model: str,
        timeout_seconds: float = 180.0,
        client: Any | None = None,
    ) -> None:
        self._base_url = base_url.rstrip("/")
        self._model = model
        self._timeout_seconds = timeout_seconds
        self._client = client

    @property
    def name(self) -> str:
        return f"ollama ({self._model})"

    @property
    def cache_namespace(self) -> str:
        return f"ollama:{self._model}"

    async def analyze(self, text: str) -> AnalysisResult:
        if self._client is None:
            self._client = httpx.AsyncClient(timeout=self._timeout_seconds)

        try:
            response = await self._client.post(
                f"{self._base_url}/api/chat",
                json={
                    "model": self._model,
                    "messages": [
                        {"role": "system", "content": SYSTEM_PROMPT},
                        {"role": "user", "content": text},
                    ],
                    "format": AnalysisResult.model_json_schema(),
                    "stream": False,
                },
            )
        except httpx.ConnectError as exc:
            raise RuntimeError(
                "Cannot connect to Ollama. Start Ollama on this Mac and make sure "
                f"the '{self._model}' model is installed."
            ) from exc

        response.raise_for_status()
        try:
            content = response.json()["message"]["content"]
            return AnalysisResult.model_validate_json(content)
        except (KeyError, TypeError, ValueError) as exc:
            raise RuntimeError("Ollama returned an invalid structured analysis") from exc
