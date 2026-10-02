from __future__ import annotations

import asyncio
import json
from collections.abc import AsyncIterator, Iterable, Mapping
from typing import Any

import httpx

from ..config import InferDocSettings
from ..exceptions import BackendError
from .models import ChatResponse, TokenUsage

Message = Mapping[str, Any]


class NebiusClient:
    """Native Nebius Token Factory HTTP client."""

    def __init__(
        self,
        settings: InferDocSettings | None = None,
        *,
        api_key: str | None = None,
        base_url: str | None = None,
        timeout_s: float | None = None,
        transport: httpx.AsyncBaseTransport | None = None,
    ) -> None:
        settings = settings or InferDocSettings.from_env()

        self.settings = InferDocSettings(
            api_key=(
                api_key
                if api_key is not None
                else settings.api_key
            ),
            base_url=base_url or settings.base_url,
            default_model=settings.default_model,
            doctor_model=settings.doctor_model,
            timeout_s=timeout_s or settings.timeout_s,
            max_retries=settings.max_retries,
            artifact_dir=settings.artifact_dir,
        )

        self.raw = httpx.AsyncClient(
            base_url=self.settings.normalized_base_url(),
            headers={
                "Authorization":
                    f"Bearer {self.settings.api_key or ''}"
            },
            timeout=self.settings.timeout_s,
            transport=transport,
        )

    async def aclose(self) -> None:
        await self.raw.aclose()

    async def __aenter__(self) -> NebiusClient:
        return self

    async def __aexit__(self, *_: object) -> None:
        await self.aclose()

    def _headers(self) -> dict[str, str]:
        self.settings.require_api_key()

        return {
            "Authorization":
                f"Bearer {self.settings.api_key}"
        }

    @staticmethod
    def _messages(
        prompt: str | None,
        messages: Iterable[Message] | None,
    ) -> list[dict[str, Any]]:
        if messages is not None:
            result = [
                dict(message)
                for message in messages
            ]

            if not result:
                raise ValueError(
                    "messages must contain at least one message"
                )

            return result

        if prompt is None:
            raise ValueError(
                "provide either prompt or messages"
            )

        return [
            {
                "role": "user",
                "content": prompt,
            }
        ]

    @staticmethod
    def _response(
        data: dict[str, Any],
    ) -> ChatResponse:
        choices = data.get("choices") or []

        text = ""
        reasoning_content: str | None = None
        finish_reason: str | None = None

        if choices:
            choice = choices[0] or {}

            message = choice.get("message") or {}
            delta = choice.get("delta") or {}

            text = (
                message.get("content")
                or delta.get("content")
                or ""
            )

            reasoning_content = (
                message.get("reasoning_content")
                or delta.get("reasoning_content")
                or None
            )

            finish_reason = choice.get(
                "finish_reason"
            )

        usage = data.get("usage") or {}

        return ChatResponse(
            text=text,
            reasoning_content=reasoning_content,
            finish_reason=finish_reason,
            model=data.get("model"),
            response_id=data.get("id"),
            usage=TokenUsage(
                prompt_tokens=usage.get(
                    "prompt_tokens"
                ),
                completion_tokens=usage.get(
                    "completion_tokens"
                ),
                total_tokens=usage.get(
                    "total_tokens"
                ),
            ),
            raw=data,
        )

    async def achat(
        self,
        *,
        model: str | None = None,
        prompt: str | None = None,
        messages: Iterable[Message] | None = None,
        stream: bool = False,
        **parameters: Any,
    ) -> ChatResponse | AsyncIterator[str]:
        payload: dict[str, Any] = {
            "model":
                model
                or self.settings.default_model,
            "messages":
                self._messages(
                    prompt,
                    messages,
                ),
            "stream": stream,
            **parameters,
        }

        if stream:
            return self._stream(payload)

        self.settings.require_api_key()

        for attempt in range(
            self.settings.max_retries + 1
        ):
            try:
                response = await self.raw.post(
                    "chat/completions",
                    json=payload,
                    headers=self._headers(),
                )

                if (
                    response.status_code >= 500
                    and attempt
                    < self.settings.max_retries
                ):
                    await asyncio.sleep(
                        0.2 * (attempt + 1)
                    )
                    continue

                if response.is_error:
                    raise BackendError(
                        "Token Factory HTTP "
                        f"{response.status_code}: "
                        f"{response.text[:500]}"
                    )

                return self._response(
                    response.json()
                )

            except httpx.HTTPError as exc:
                if (
                    attempt
                    >= self.settings.max_retries
                ):
                    raise BackendError(
                        "Token Factory connection "
                        f"failed: {exc}"
                    ) from exc

                await asyncio.sleep(
                    0.2 * (attempt + 1)
                )

        raise AssertionError("unreachable")

    async def _stream(
        self,
        payload: dict[str, Any],
    ) -> AsyncIterator[str]:
        self.settings.require_api_key()

        try:
            async with self.raw.stream(
                "POST",
                "chat/completions",
                json=payload,
                headers=self._headers(),
            ) as response:

                if response.is_error:
                    body = await response.aread()

                    raise BackendError(
                        "Token Factory HTTP "
                        f"{response.status_code}: "
                        f"{body[:500]!r}"
                    )

                async for line in (
                    response.aiter_lines()
                ):
                    if not line.startswith(
                        "data:"
                    ):
                        continue

                    data = line[5:].strip()

                    if data == "[DONE]":
                        break

                    try:
                        item = json.loads(data)

                    except json.JSONDecodeError:
                        continue

                    choices = (
                        item.get("choices")
                        or []
                    )

                    if not choices:
                        continue

                    delta = (
                        choices[0].get("delta")
                        or {}
                    )

                    text = (
                        delta.get("content")
                        or ""
                    )

                    if text:
                        yield text

        except httpx.HTTPError as exc:
            raise BackendError(
                "Token Factory streaming "
                f"connection failed: {exc}"
            ) from exc

    async def astream(
        self,
        **kwargs: Any,
    ) -> AsyncIterator[str]:
        result = await self.achat(
            stream=True,
            **kwargs,
        )

        assert hasattr(
            result,
            "__aiter__",
        )

        async for item in result:
            yield item

    def chat(
        self,
        **kwargs: Any,
    ) -> ChatResponse:
        """Perform one sync request and close on the same event loop."""

        if kwargs.get("stream"):
            raise ValueError(
                "NebiusClient.chat() is "
                "non-streaming; use "
                "achat()/astream() for streaming"
            )

        async def _run_once() -> ChatResponse:
            try:
                result = await self.achat(
                    **kwargs
                )

                if not isinstance(
                    result,
                    ChatResponse,
                ):
                    raise TypeError(
                        "synchronous chat expected "
                        "a non-streaming ChatResponse"
                    )

                return result

            finally:
                await self.aclose()

        return asyncio.run(
            _run_once()
        )


def chat(
    **kwargs: Any,
) -> ChatResponse:
    """One-shot synchronous Token Factory chat."""

    return NebiusClient().chat(
        **kwargs
    )