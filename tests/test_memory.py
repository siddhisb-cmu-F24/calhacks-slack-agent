from __future__ import annotations

import pytest
import httpx
from httpx import AsyncClient

from app.main import app
from app.config import settings


@pytest.mark.asyncio
async def test_memory_upsert_and_search(monkeypatch: pytest.MonkeyPatch, respx_mock):
    vector = [0.01] * settings.embedding_dim
    respx_mock.post(str(settings.embedding_api_url)).mock(
        side_effect=[
            httpx.Response(200, json={"embedding": vector}),
            httpx.Response(200, json={"embedding": vector}),
        ]
    )

    async def fake_insert(row):
        assert row["channel"] == "C123"
        assert row["embedding"] == vector
        return 42

    async def fake_search(**kwargs):
        assert kwargs["k"] == 5
        return [
            {
                "id": 42,
                "score": 0.12,
                "q_text": "How to request VPN?",
                "a_text": "Use the IT portal",
                "source_url": "https://confluence/vpn",
                "ts": "2024-01-01T00:00:00Z",
            }
        ]

    monkeypatch.setattr("app.routers.memory.insert_memory", fake_insert)
    monkeypatch.setattr("app.routers.memory.search_memory", fake_search)

    async with AsyncClient(app=app, base_url="http://test") as client:
        upsert_payload = {
            "channel": "C123",
            "q_text": "How to request VPN?",
            "a_text": "Visit the IT portal",
            "source_url": "https://confluence/vpn",
        }
        resp = await client.post("/memory/upsert", json=upsert_payload)
        assert resp.status_code == 200
        assert resp.json() == {"id": 42}

        search_payload = {"channel": "C123", "query": "VPN", "k": 5}
        resp = await client.post("/memory/search", json=search_payload)
        assert resp.status_code == 200
        data = resp.json()
        assert data["matches"][0]["score"] == pytest.approx(0.12)
