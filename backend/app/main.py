import logging
from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.computer_control import MacComputerController, plan_from_consensus
from app.database import create_tables, get_session, save_analysis
from app.orchestrator import MultiAIOrchestrator
from app.providers import AIProvider, get_ai_provider, get_ai_providers
from app.schemas import (
    ActionPlan,
    AnalysisResult,
    AnalyzeRequest,
    AnalyzeResponse,
    ExecuteActionRequest,
    ExecuteActionResponse,
    MultiAnalyzeResponse,
)
from app.services import get_cached, set_cached, text_hash

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(_: FastAPI):
    try:
        await create_tables()
    except Exception:
        logger.exception("Database initialization failed")
    yield


settings = get_settings()
app = FastAPI(title=settings.app_name, version="0.1.0", lifespan=lifespan)


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/api/v1/analyze", response_model=AnalyzeResponse)
async def analyze(
    request: AnalyzeRequest,
    session: AsyncSession = Depends(get_session),
    provider: AIProvider = Depends(get_ai_provider),
) -> AnalyzeResponse:
    key = f"analysis:{provider.cache_namespace}:{text_hash(request.text)}"

    try:
        cached = await get_cached(key)
        if cached:
            return AnalyzeResponse(
                analysis=cached, provider=provider.name, cached=True
            )
    except Exception:
        logger.exception("Cache read failed")

    try:
        result = await provider.analyze(request.text)
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except Exception as exc:
        logger.exception("AI analysis failed")
        raise HTTPException(status_code=502, detail="AI analysis failed") from exc

    try:
        await set_cached(key, result)
    except Exception:
        logger.exception("Cache write failed")

    try:
        await save_analysis(
            session,
            input_hash=text_hash(request.text),
            input_text=request.text,
            result_json=result.model_dump_json(),
        )
    except Exception:
        logger.exception("Database write failed")
        await session.rollback()

    return AnalyzeResponse(analysis=result, provider=provider.name)


@app.post("/api/v1/analyze/multi", response_model=MultiAnalyzeResponse)
async def analyze_multi(
    request: AnalyzeRequest,
    providers: list[AIProvider] = Depends(get_ai_providers),
) -> MultiAnalyzeResponse:
    try:
        results, consensus = await MultiAIOrchestrator(providers).analyze(request.text)
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc

    succeeded = sum(result.analysis is not None for result in results)
    return MultiAnalyzeResponse(
        results=results,
        consensus=consensus,
        providers_succeeded=succeeded,
        providers_failed=len(results) - succeeded,
    )


@app.post("/api/v1/actions/plan", response_model=ActionPlan)
async def plan_actions(consensus: AnalysisResult) -> ActionPlan:
    return plan_from_consensus(consensus)


@app.post("/api/v1/actions/execute", response_model=ExecuteActionResponse)
async def execute_action(request: ExecuteActionRequest) -> ExecuteActionResponse:
    current = get_settings()
    controller = MacComputerController(
        enabled=current.enable_computer_control,
        allowed_apps={
            app_name.strip()
            for app_name in current.allowed_apps.split(",")
            if app_name.strip()
        },
    )
    return await controller.execute(request.action, request.approved)
