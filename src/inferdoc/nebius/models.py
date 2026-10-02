from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class TokenUsage(BaseModel):
    prompt_tokens: int | None = None
    completion_tokens: int | None = None
    total_tokens: int | None = None


class ChatResponse(BaseModel):
    model_config = ConfigDict(extra="allow")

    text: str = ""
    reasoning_content: str | None = None
    finish_reason: str | None = None

    model: str | None = None
    response_id: str | None = None

    usage: TokenUsage = Field(default_factory=TokenUsage)

    raw: dict[str, Any] = Field(default_factory=dict)
