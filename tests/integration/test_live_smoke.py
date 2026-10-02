import os

import pytest

import inferdoc
from inferdoc.config import InferDocSettings


@pytest.mark.integration
def test_live_token_factory_smoke() -> None:
    settings = InferDocSettings.from_env()

    if (
        os.getenv(
            "INFERDOC_RUN_LIVE_TESTS"
        )
        != "1"
        or not settings.api_key
    ):
        pytest.skip(
            "set INFERDOC_RUN_LIVE_TESTS=1 "
            "and NEBIUS_API_KEY in .env or "
            "the process environment to "
            "spend live credits"
        )

    result = inferdoc.chat(
        model=settings.default_model,
        prompt=(
            "Reply with exactly the word: ready"
        ),
        max_tokens=32,
        temperature=0,
        chat_template_kwargs={
            "enable_thinking": False,
        },
    )

    assert (
        result.model is None
        or result.model
        == settings.default_model
        or "Nemotron-3-Nano-30B-A3B"
        in result.model
    )

    assert result.text.strip(), (
        "Token Factory returned no final text; "
        f"finish_reason="
        f"{result.finish_reason!r}, "
        f"reasoning_content="
        f"{result.reasoning_content!r}, "
        f"raw={result.raw!r}"
    )

    assert (
        "ready"
        in result.text.lower()
    )