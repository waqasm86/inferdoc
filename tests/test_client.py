import asyncio
import json

import httpx
import pytest

from inferdoc.nebius.client import (
    NebiusClient,
)


def test_client_normalizes_openai_compatible_response() -> None:
    async def handler(
        request: httpx.Request,
    ) -> httpx.Response:
        assert (
            request.headers[
                "authorization"
            ]
            == "Bearer secret"
        )

        body = json.loads(
            request.content
        )

        assert (
            body["model"]
            == "test-model"
        )

        return httpx.Response(
            200,
            json={
                "id": "x",
                "model": "test-model",
                "choices": [
                    {
                        "finish_reason":
                            "stop",
                        "message": {
                            "content":
                                "ok"
                        },
                    }
                ],
                "usage": {
                    "prompt_tokens": 2,
                    "completion_tokens": 1,
                    "total_tokens": 3,
                },
            },
        )

    async def run() -> None:
        async with NebiusClient(
            api_key="secret",
            base_url=(
                "https://example.test/v1"
            ),
            transport=(
                httpx.MockTransport(
                    handler
                )
            ),
        ) as client:

            result = await client.achat(
                model="test-model",
                prompt="hello",
                max_tokens=2,
            )

            assert result.text == "ok"

            assert (
                result.finish_reason
                == "stop"
            )

            assert (
                result.usage
                .completion_tokens
                == 1
            )

    asyncio.run(run())


def test_streaming_collects_sse_chunks() -> None:
    async def handler(
        request: httpx.Request,
    ) -> httpx.Response:
        content = (
            'data: {"choices":'
            '[{"delta":{"content":"a"}}]}'
            "\n\n"
            'data: {"choices":'
            '[{"delta":{"content":"b"}}]}'
            "\n\n"
            "data: [DONE]\n\n"
        )

        return httpx.Response(
            200,
            content=content,
            headers={
                "content-type":
                    "text/event-stream"
            },
        )

    async def run() -> list[str]:
        async with NebiusClient(
            api_key="secret",
            transport=(
                httpx.MockTransport(
                    handler
                )
            ),
        ) as client:

            result = await client.achat(
                prompt="hello",
                stream=True,
            )

            return [
                chunk
                async for chunk
                in result
            ]

    assert (
        asyncio.run(run())
        == ["a", "b"]
    )


def test_sync_chat_closes_on_same_event_loop() -> None:
    async def handler(
        request: httpx.Request,
    ) -> httpx.Response:
        return httpx.Response(
            200,
            json={
                "id": "sync",
                "model": "test-model",
                "choices": [
                    {
                        "finish_reason":
                            "stop",
                        "message": {
                            "content":
                                "ready"
                        },
                    }
                ],
                "usage": {
                    "prompt_tokens": 1,
                    "completion_tokens": 1,
                    "total_tokens": 2,
                },
            },
        )

    client = NebiusClient(
        api_key="secret",
        base_url=(
            "https://example.test/v1"
        ),
        transport=(
            httpx.MockTransport(
                handler
            )
        ),
    )

    result = client.chat(
        model="test-model",
        prompt="hello",
        max_tokens=4,
    )

    assert (
        result.text
        == "ready"
    )

    assert client.raw.is_closed


def test_sync_chat_rejects_streaming() -> None:
    client = NebiusClient(
        api_key="secret",
        base_url=(
            "https://example.test/v1"
        ),
        transport=httpx.MockTransport(
            lambda request:
                httpx.Response(
                    200,
                    json={},
                )
        ),
    )

    with pytest.raises(
        ValueError,
        match="non-streaming",
    ):
        client.chat(
            prompt="hello",
            stream=True,
        )

    asyncio.run(
        client.aclose()
    )


def test_client_forwards_chat_template_kwargs_and_parses_reasoning() -> None:
    async def handler(
        request: httpx.Request,
    ) -> httpx.Response:
        body = json.loads(
            request.content
        )

        assert (
            body[
                "chat_template_kwargs"
            ]
            == {
                "enable_thinking":
                    False
            }
        )

        return httpx.Response(
            200,
            json={
                "id": "reasoning",
                "model": "test-model",
                "choices": [
                    {
                        "finish_reason":
                            "stop",
                        "message": {
                            "content":
                                "ready",
                            "reasoning_content":
                                "internal reasoning",
                        },
                    }
                ],
                "usage": {
                    "prompt_tokens": 1,
                    "completion_tokens": 2,
                    "total_tokens": 3,
                },
            },
        )

    async def run() -> None:
        async with NebiusClient(
            api_key="secret",
            base_url=(
                "https://example.test/v1"
            ),
            transport=(
                httpx.MockTransport(
                    handler
                )
            ),
        ) as client:

            result = await client.achat(
                model="test-model",
                prompt="hello",
                chat_template_kwargs={
                    "enable_thinking":
                        False
                },
            )

            assert (
                result.text
                == "ready"
            )

            assert (
                result.reasoning_content
                == "internal reasoning"
            )

            assert (
                result.finish_reason
                == "stop"
            )

    asyncio.run(run())