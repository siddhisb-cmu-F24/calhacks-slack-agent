"""Slack reply endpoint."""
from __future__ import annotations

from typing import List

from fastapi import APIRouter, HTTPException, status
import httpx
from loguru import logger

from ..config import settings
from ..deps import get_http_client
from ..domain import policy
from ..domain.schemas import SlackReplyRequest, SlackReplyResponse

router = APIRouter(prefix="/slack", tags=["slack"])


def _build_message(payload: SlackReplyRequest) -> str:
    words = payload.answer.split()
    if len(words) > policy.MAX_ANSWER_WORDS:
        trimmed = " ".join(words[: policy.MAX_ANSWER_WORDS])
        logger.warning("answer truncated to policy limit")
    else:
        trimmed = payload.answer

    lines: List[str] = [f"[Auto-Reply] {trimmed.strip()}"]
    refs = payload.references[: policy.MAX_SOURCES]
    if refs:
        lines.append("Sources:")
        for ref in refs:
            lines.append(f"• <{ref.url}|{ref.title}>")

    if payload.mode == "followup" and "?" not in trimmed:
        lines.append("Clarifying question: Could you share a bit more detail?")

    lines.append(f"Confidence: {payload.confidence:.2f}")
    return "\n".join(lines)


@router.post("/reply", response_model=SlackReplyResponse)
async def post_slack_reply(payload: SlackReplyRequest) -> SlackReplyResponse:
    message = _build_message(payload)
    body = {
        "channel": payload.channel,
        "text": message,
        "thread_ts": payload.thread_ts,
        "mrkdwn": True,
    }
    if settings.slack_post_as_user:
        body["as_user"] = True

    headers = {
        "Authorization": f"Bearer {settings.slack_bot_token}",
        "Content-Type": "application/json; charset=utf-8",
    }

    client = get_http_client()
    response = await client.post("https://slack.com/api/chat.postMessage", json=body, headers=headers)

    if response.status_code == status.HTTP_429_TOO_MANY_REQUESTS:
        retry_after = response.headers.get("Retry-After", "1")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Slack rate limit hit. Retry after {retry_after}s",
        )

    try:
        response.raise_for_status()
    except httpx.HTTPStatusError as exc:
        logger.exception("Slack API error: {}", exc.response.text)
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail="Slack API error") from exc

    data = response.json()
    if not data.get("ok"):
        logger.error("Slack API returned failure: {}", data)
        raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY, detail="Slack API rejected the message")

    return SlackReplyResponse(ok=True, ts=data.get("ts", payload.thread_ts))
