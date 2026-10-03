from __future__ import annotations

import hashlib
import json

from redis.asyncio import Redis

from app.config import get_settings
from app.schemas import AnalysisResult

def text_hash(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


async def get_cached(key: str) -> AnalysisResult | None:
    settings = get_settings()
    client = Redis.from_url(settings.redis_url, decode_responses=True)
    try:
        value = await client.get(key)
        return AnalysisResult.model_validate_json(value) if value else None
    finally:
        await client.aclose()


async def set_cached(key: str, result: AnalysisResult) -> None:
    settings = get_settings()
    client = Redis.from_url(settings.redis_url, decode_responses=True)
    try:
        await client.set(
            key,
            json.dumps(result.model_dump(mode="json"), ensure_ascii=False),
            ex=settings.cache_ttl_seconds,
        )
    finally:
        await client.aclose()
