import asyncio

from app.providers.base import AIProvider
from app.schemas import AnalysisResult, ProviderAnalysis, Severity


class MultiAIOrchestrator:
    """Runs providers concurrently and combines their structured results."""

    def __init__(self, providers: list[AIProvider]):
        if not providers:
            raise ValueError("At least one AI provider is required")
        self.providers = providers

    async def analyze(self, text: str) -> tuple[list[ProviderAnalysis], AnalysisResult]:
        outcomes = await asyncio.gather(
            *(provider.analyze(text) for provider in self.providers),
            return_exceptions=True,
        )
        results: list[ProviderAnalysis] = []
        successful: list[AnalysisResult] = []

        for provider, outcome in zip(self.providers, outcomes):
            if isinstance(outcome, BaseException):
                results.append(
                    ProviderAnalysis(provider=provider.name, error=str(outcome))
                )
            else:
                successful.append(outcome)
                results.append(
                    ProviderAnalysis(provider=provider.name, analysis=outcome)
                )

        if not successful:
            raise RuntimeError("All AI providers failed")
        return results, self._consensus(successful)

    @staticmethod
    def _consensus(results: list[AnalysisResult]) -> AnalysisResult:
        severity_order = {
            Severity.info: 0,
            Severity.warning: 1,
            Severity.critical: 2,
        }

        def unique(items: list[str]) -> list[str]:
            return list(dict.fromkeys(items))

        return AnalysisResult(
            summary=" / ".join(unique([result.summary for result in results])),
            severity=max(results, key=lambda result: severity_order[result.severity]).severity,
            likely_causes=unique(
                [cause for result in results for cause in result.likely_causes]
            ),
            recommended_actions=unique(
                [action for result in results for action in result.recommended_actions]
            ),
        )
