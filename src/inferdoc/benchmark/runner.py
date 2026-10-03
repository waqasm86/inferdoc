from __future__ import annotations

import asyncio
import time
import uuid
from collections.abc import Iterable
from datetime import UTC, datetime
from importlib.metadata import (
    PackageNotFoundError,
    version,
)
from typing import Any, Protocol

from pydantic import BaseModel, Field

from ..evidence.models import (
    EvidenceBundle,
    RequestMeasurement,
)
from ..evidence.provenance import (
    canonical_sha256,
    runtime_provenance,
)
from ..nebius.client import NebiusClient
from .workload import WorkloadSpec


def _inferdoc_version() -> str:
    try:
        return version("inferdoc")
    except PackageNotFoundError:
        return "0+unknown"


class ChatLike(Protocol):
    async def achat(
        self,
        **kwargs: Any,
    ) -> Any: ...


class BenchmarkLimits(BaseModel):
    max_requests: int = Field(
        default=32,
        ge=1,
    )

    timeout_s: float = Field(
        default=120.0,
        gt=0,
    )


class AsyncBenchmarkRunner:
    def __init__(
        self,
        client: ChatLike,
        *,
        limits: BenchmarkLimits | None = None,
    ) -> None:
        self.client = client
        self.limits = (
            limits
            or BenchmarkLimits()
        )

    async def _one(
        self,
        prompt: str,
        index: int,
        workload: WorkloadSpec,
        model: str | None,
    ) -> RequestMeasurement:
        request_id = (
            f"req-{index:04d}-"
            f"{uuid.uuid4().hex[:8]}"
        )

        started = datetime.now(UTC)

        first: datetime | None = None

        output_text = ""

        try:
            result = await asyncio.wait_for(
                self.client.achat(
                    model=model,
                    prompt=prompt,
                    stream=workload.stream,
                    max_tokens=(
                        workload.max_tokens
                    ),
                    temperature=(
                        workload.temperature
                    ),
                    chat_template_kwargs={
                        "enable_thinking":
                            workload.enable_thinking
                    },
                ),
                timeout=(
                    self.limits.timeout_s
                ),
            )

            if hasattr(
                result,
                "__aiter__",
            ):
                async for chunk in result:
                    if first is None:
                        first = datetime.now(UTC)

                    output_text += str(chunk)

                usage: dict[str, Any] = {}

                response_model = None

            else:
                first = None

                output_text = getattr(
                    result,
                    "text",
                    "",
                )

                usage_model = getattr(
                    result,
                    "usage",
                    None,
                )

                usage = (
                    usage_model.model_dump()
                    if hasattr(
                        usage_model,
                        "model_dump",
                    )
                    else (
                        usage_model
                        or {}
                    )
                )

                response_model = getattr(
                    result,
                    "model",
                    None,
                )

            finished = datetime.now(UTC)

            return RequestMeasurement(
                request_id=request_id,
                prompt=prompt,
                prompt_sha256=(
                    canonical_sha256(
                        prompt
                    )
                ),
                prompt_length=len(prompt),
                started_at=started,
                first_response_at=first,
                finished_at=finished,
                success=True,
                input_tokens=usage.get(
                    "prompt_tokens"
                ),
                output_tokens=usage.get(
                    "completion_tokens"
                ),
                total_tokens=usage.get(
                    "total_tokens"
                ),
                model=response_model,
            )

        except Exception as exc:
            finished = datetime.now(UTC)

            return RequestMeasurement(
                request_id=request_id,
                prompt=prompt,
                prompt_sha256=(
                    canonical_sha256(
                        prompt
                    )
                ),
                prompt_length=len(prompt),
                started_at=started,
                first_response_at=first,
                finished_at=finished,
                success=False,
                error=(
                    f"{type(exc).__name__}: "
                    f"{exc}"
                ),
            )

    async def run(
        self,
        workload: WorkloadSpec,
        *,
        model: str | None = None,
    ) -> EvidenceBundle:
        if (
            len(workload.prompts)
            > self.limits.max_requests
        ):
            raise ValueError(
                "workload has "
                f"{len(workload.prompts)} "
                "requests; limit is "
                f"{self.limits.max_requests}"
            )

        created = datetime.now(UTC)

        started_perf = time.perf_counter()

        semaphore = asyncio.Semaphore(
            workload.concurrency
        )

        async def guarded(
            prompt: str,
            index: int,
        ) -> RequestMeasurement:
            async with semaphore:
                return await self._one(
                    prompt,
                    index,
                    workload,
                    model,
                )

        requests = await asyncio.gather(
            *(
                guarded(
                    prompt,
                    index,
                )
                for index, prompt
                in enumerate(
                    workload.prompts
                )
            )
        )

        elapsed_s = max(
            time.perf_counter()
            - started_perf,
            1e-9,
        )

        completed = datetime.now(UTC)

        model_name = (
            model
            or getattr(
                getattr(
                    self.client,
                    "settings",
                    None,
                ),
                "default_model",
                "unknown",
            )
        )

        parameters = workload.model_dump(
            exclude={
                "prompts",
                "concurrency",
            }
        )

        return (
            EvidenceBundle.with_aggregate(
                run_id=(
                    "run-"
                    f"{created.strftime('%Y%m%dT%H%M%S')}-"
                    f"{uuid.uuid4().hex[:8]}"
                ),
                backend=(
                    "nebius-token-factory"
                ),
                model=model_name,
                created_at=created,
                completed_at=completed,
                parameters=parameters,
                workload=(
                    workload.model_dump()
                ),
                requests=requests,
                elapsed_s=elapsed_s,
                provenance={
                    "config_sha256":
                        canonical_sha256(
                            workload.model_dump()
                        ),
                    **runtime_provenance(
                        workload=(
                            workload.model_dump()
                        ),
                        provider=(
                            "nebius-token-factory"
                        ),
                        endpoint_host=(
                            "api.tokenfactory."
                            "nebius.com"
                        ),
                        inferdoc_version=(
                            _inferdoc_version()
                        ),
                    ),
                },
            )
        )


def benchmark(
    *,
    model: str | None = None,
    prompts: Iterable[str],
    concurrency: int = 1,
    max_tokens: int = 64,
    temperature: float = 0.0,
    stream: bool = False,
    enable_thinking: bool = False,
    client: ChatLike | None = None,
    limits: BenchmarkLimits | None = None,
) -> EvidenceBundle:
    workload = WorkloadSpec(
        prompts=list(prompts),
        concurrency=concurrency,
        max_tokens=max_tokens,
        temperature=temperature,
        stream=stream,
        enable_thinking=enable_thinking,
    )

    owned = client is None

    actual = (
        client
        or NebiusClient()
    )

    async def _run_once() -> EvidenceBundle:
        try:
            return await AsyncBenchmarkRunner(
                actual,
                limits=limits,
            ).run(
                workload,
                model=model,
            )

        finally:
            if (
                owned
                and hasattr(
                    actual,
                    "aclose",
                )
            ):
                await actual.aclose()

    return asyncio.run(
        _run_once()
    )
