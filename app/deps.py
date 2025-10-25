"""Application-wide dependency singletons."""
from __future__ import annotations

from typing import Optional

import httpx
from supabase import Client, create_client

from .config import settings

_http_client: Optional[httpx.AsyncClient] = None
_supabase_client: Optional[Client] = None


def get_http_client() -> httpx.AsyncClient:
    """Return a shared AsyncClient with sane defaults."""

    global _http_client
    if _http_client is None:
        timeout = httpx.Timeout(connect=5.0, read=20.0, write=5.0, pool=5.0)
        transport = httpx.AsyncHTTPTransport(retries=3)
        _http_client = httpx.AsyncClient(timeout=timeout, transport=transport)
    return _http_client


def get_supabase_client() -> Client:
    """Return a lazily constructed Supabase client."""

    global _supabase_client
    if _supabase_client is None:
        _supabase_client = create_client(str(settings.supabase_url), settings.supabase_service_role_key)
    return _supabase_client


async def shutdown_dependencies() -> None:
    """Clean up network clients on application shutdown."""

    global _http_client
    if _http_client is not None:
        await _http_client.aclose()
        _http_client = None
