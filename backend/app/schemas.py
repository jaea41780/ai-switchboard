from __future__ import annotations

from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


class Severity(str, Enum):
    info = "info"
    warning = "warning"
    critical = "critical"


class AnalyzeRequest(BaseModel):
    text: str = Field(min_length=10, max_length=50_000)


class AnalysisResult(BaseModel):
    summary: str
    severity: Severity
    likely_causes: list[str]
    recommended_actions: list[str]


class AnalyzeResponse(BaseModel):
    analysis: AnalysisResult
    provider: str
    cached: bool = False


class ProviderAnalysis(BaseModel):
    provider: str
    analysis: Optional[AnalysisResult] = None
    error: Optional[str] = None


class MultiAnalyzeResponse(BaseModel):
    results: list[ProviderAnalysis]
    consensus: AnalysisResult
    providers_succeeded: int
    providers_failed: int


class ActionType(str, Enum):
    open_app = "open_app"
    open_url = "open_url"
    notify = "notify"


class ComputerAction(BaseModel):
    type: ActionType
    target: str = Field(min_length=1, max_length=2_000)
    reason: str = Field(min_length=1, max_length=1_000)


class ActionPlan(BaseModel):
    summary: str
    actions: list[ComputerAction]
    requires_approval: bool = True


class ExecuteActionRequest(BaseModel):
    action: ComputerAction
    approved: bool = False


class ExecuteActionResponse(BaseModel):
    status: str
    message: str
