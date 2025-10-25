from __future__ import annotations

import pytest
import httpx
from httpx import AsyncClient

from app.main import app


@pytest.mark.asyncio
async def test_slack_reply(monkeypatch: pytest.MonkeyPatch, respx_mock):
    route = respx_mock.post("https://slack.com/api/chat.postMessage").mock(
        return_value=httpx.Response(200, json={"ok": True, "ts": "1729900455.444"})
    )

    async with AsyncClient(app=app, base_url="http://test") as client:
        payload = {
            "channel": "C123",
            "thread_ts": "1729900314.123",
            "answer": "Here is how to request VPN access.",
            "references": [{"title": "VPN SOP", "url": "https://example.com/vpn"}],
            "mode": "answer",
            "confidence": 0.9,
        }
        resp = await client.post("/slack/reply", json=payload)

    assert resp.status_code == 200
    body = resp.json()
    assert body["ok"] is True
    assert body["ts"] == "1729900455.444"
    sent = route.calls.last.request.json()
    assert sent["channel"] == "C123"
    assert sent["thread_ts"] == "1729900314.123"
    assert "[Auto-Reply]" in sent["text"]
    assert "Confidence: 0.90" in sent["text"]
