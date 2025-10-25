"""Helpers around Supabase data access."""
from __future__ import annotations

import asyncio
from typing import Any, Dict, List, Optional

from loguru import logger

from .config import settings
from .deps import get_http_client, get_supabase_client


async def insert_memory(row: Dict[str, Any]) -> int:
    """Insert a memory row via the Supabase client."""

    def _insert_sync() -> int:
        client = get_supabase_client()
        response = client.table(settings.supabase_table).insert(row).execute()
        data = getattr(response, "data", None) or []
        if not data:
            raise RuntimeError("Supabase insert returned no data")
        memory_id = data[0].get("id")
        if memory_id is None:
            raise RuntimeError("Supabase insert did not return an id")
        return int(memory_id)

    return await asyncio.to_thread(_insert_sync)


async def search_memory(
    *, channel: Optional[str], query_embedding: List[float], k: int
) -> List[Dict[str, Any]]:
    """Call a Postgres RPC that performs pgvector similarity search."""

    if k <= 0:
        return []

    url = f"{str(settings.supabase_url).rstrip('/')}/rest/v1/rpc/{settings.supabase_search_function}"
    headers = {
        "apikey": settings.supabase_service_role_key,
        "Authorization": f"Bearer {settings.supabase_service_role_key}",
        "Content-Type": "application/json",
        "Accept": "application/json",
        "Prefer": "return=representation",
    }
    payload: Dict[str, Any] = {
        "query_embedding": query_embedding,
        "match_count": k,
    }
    if channel:
        payload["channel_filter"] = channel

    http_client = get_http_client()
    response = await http_client.post(url, json=payload, headers=headers)
    response.raise_for_status()
    data = response.json()
    if not isinstance(data, list):
        logger.error("Unexpected RPC response: {}", data)
        raise RuntimeError("Supabase RPC returned unexpected payload")

    matches: List[Dict[str, Any]] = []
    for row in data:
        try:
            matches.append(
                {
                    "id": int(row["id"]),
                    "q_text": row["q_text"],
                    "a_text": row["a_text"],
                    "source_url": row.get("source_url"),
                    "ts": row.get("ts"),
                    "score": float(row.get("distance", 0.0)),
                }
            )
        except KeyError as exc:
            logger.error("RPC row missing field: {}", exc)
    return matches
