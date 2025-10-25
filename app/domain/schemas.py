"""Pydantic schemas for request and response payloads."""
from __future__ import annotations

from datetime import datetime
from typing import Literal, Optional

from pydantic import BaseModel, ConfigDict, Field


class ProblemDetails(BaseModel):
    model_config = ConfigDict(extra="forbid")

    title: str
    detail: str
    status: int


class UpsertRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    channel: str = Field(min_length=1)
    q_text: str = Field(min_length=1)
    a_text: str = Field(min_length=1)
    source_url: Optional[str] = None
    ts: Optional[datetime] = None


class UpsertResponse(BaseModel):
    id: int


class SearchRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    channel: Optional[str] = None
    query: str = Field(min_length=1)
    k: int = Field(default=5, ge=1, le=20)


class Match(BaseModel):
    id: int
    score: float
    q_text: str
    a_text: str
    source_url: Optional[str] = None
    ts: Optional[datetime] = None


class SearchResponse(BaseModel):
    matches: list[Match]


class Reference(BaseModel):
    title: str = Field(min_length=1)
    url: str = Field(min_length=1)


class SlackReplyRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    channel: str = Field(min_length=1)
    thread_ts: str = Field(min_length=1)
    answer: str = Field(min_length=1, max_length=1200)
    references: list[Reference] = Field(default_factory=list)
    mode: Literal["answer", "followup"]
    confidence: float = Field(ge=0.0, le=1.0)


class SlackReplyResponse(BaseModel):
    ok: bool
    ts: str
