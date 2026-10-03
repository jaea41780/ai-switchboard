from typing import Protocol

from app.schemas import AnalysisResult


class AIProvider(Protocol):
    """Contract implemented by every AI backend."""

    @property
    def name(self) -> str:
        ...

    @property
    def cache_namespace(self) -> str:
        ...

    async def analyze(self, text: str) -> AnalysisResult:
        ...
