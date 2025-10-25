"""Utility for fetching embeddings from the configured provider."""
from __future__ import annotations

from typing import List

import httpx

from .config import settings
from .deps import get_http_client


class EmbeddingError(RuntimeError):
    """Raised when the embedding provider response is invalid."""


async def embed(text: str, *, client: httpx.AsyncClient | None = None) -> List[float]:
    """Generate an embedding for the provided text."""

    if not text:
        raise EmbeddingError("text must be non-empty")

    http_client = client or get_http_client()
    response = await http_client.post(
        str(settings.embedding_api_url),
        json={"text": text},
        headers={"Authorization": f"Bearer {settings.embedding_api_key}"},
    )
    response.raise_for_status()
    payload = response.json()
    embedding = payload.get("embedding")
    if not isinstance(embedding, list):
        raise EmbeddingError("embedding payload missing or invalid")
    if len(embedding) != settings.embedding_dim:
        raise EmbeddingError(
            f"embedding dimension mismatch (expected {settings.embedding_dim}, got {len(embedding)})"
        )
    try:
        vector = [float(value) for value in embedding]
    except (TypeError, ValueError) as exc:
        raise EmbeddingError("embedding values must be numeric") from exc
    return vector
