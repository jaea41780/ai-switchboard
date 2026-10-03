from app.schemas import AnalysisResult, Severity


class FakeProvider:
    """Deterministic provider for local development and tests."""

    @property
    def name(self) -> str:
        return "fake"

    @property
    def cache_namespace(self) -> str:
        return self.name

    async def analyze(self, text: str) -> AnalysisResult:
        lowered = text.lower()
        severity = (
            Severity.critical
            if any(word in lowered for word in ("fatal", "crash", "critical"))
            else Severity.warning
        )
        return AnalysisResult(
            summary="Deterministic local analysis",
            severity=severity,
            likely_causes=["Fake provider selected for local development"],
            recommended_actions=["Set AI_PROVIDER=openai for model analysis"],
        )
