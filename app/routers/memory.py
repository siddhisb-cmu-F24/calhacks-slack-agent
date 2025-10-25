"""Memory management endpoints."""
from __future__ import annotations

from loguru import logger
from fastapi import APIRouter, HTTPException, status
import httpx

from ..embeddings import EmbeddingError, embed
from ..domain.schemas import Match, SearchRequest, SearchResponse, UpsertRequest, UpsertResponse
from ..supa import insert_memory, search_memory

router = APIRouter(prefix="/memory", tags=["memory"])


@router.post("/upsert", response_model=UpsertResponse)
async def upsert_memory(payload: UpsertRequest) -> UpsertResponse:
    try:
        vector = await embed(payload.q_text)
    except (EmbeddingError, httpx.HTTPError) as exc:
        logger.exception("embedding failed")
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=str(exc)) from exc

    row = {
        "channel": payload.channel,
        "q_text": payload.q_text,
        "a_text": payload.a_text,
        "source_url": payload.source_url,
        "ts": payload.ts.isoformat() if payload.ts else None,
        "embedding": vector,
    }

    try:
        memory_id = await insert_memory(row)
    except Exception as exc:  # pragma: no cover - network failure path
        logger.exception("supabase insert failed")
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail="Unable to insert memory") from exc

    return UpsertResponse(id=memory_id)


@router.post("/search", response_model=SearchResponse)
async def search_memories(payload: SearchRequest) -> SearchResponse:
    try:
        vector = await embed(payload.query)
    except (EmbeddingError, httpx.HTTPError) as exc:
        logger.exception("embedding failed")
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail=str(exc)) from exc

    try:
        rows = await search_memory(channel=payload.channel, query_embedding=vector, k=payload.k)
    except httpx.HTTPStatusError as exc:
        logger.exception("supabase RPC failed")
        raise HTTPException(status_code=exc.response.status_code, detail="Supabase RPC failed") from exc
    except httpx.HTTPError as exc:
        logger.exception("supabase network error")
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail="Supabase network error") from exc

    matches = [Match(**row) for row in rows]
    return SearchResponse(matches=matches)
