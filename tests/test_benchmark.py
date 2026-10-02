import asyncio
from datetime import UTC, datetime

from inferdoc.benchmark.runner import (
    AsyncBenchmarkRunner,
)
from inferdoc.benchmark.workload import (
    WorkloadSpec,
)
from inferdoc.evidence.models import (
    EvidenceBundle,
    RequestMeasurement,
)
from inferdoc.nebius.models import (
    ChatResponse,
    TokenUsage,
)


class FakeClient:
    async def achat(self, **kwargs):
        assert (
            kwargs["model"]
            == "test-model"
        )

        assert (
            kwargs["stream"]
            is False
        )

        assert (
            kwargs["max_tokens"]
            == 4
        )

        assert (
            kwargs["temperature"]
            == 0.0
        )

        assert (
            kwargs[
                "chat_template_kwargs"
            ]
            == {
                "enable_thinking":
                    False,
            }
        )

        return ChatResponse(
            text="answer",
            model="test-model",
            finish_reason="stop",
            usage=TokenUsage(
                prompt_tokens=3,
                completion_tokens=2,
                total_tokens=5,
            ),
        )


def test_benchmark_aggregates_usage_and_failures() -> None:
    workload = WorkloadSpec(
        prompts=["a", "b"],
        concurrency=2,
        max_tokens=4,
        temperature=0.0,
        stream=False,
        enable_thinking=False,
    )

    run = asyncio.run(
        AsyncBenchmarkRunner(
            FakeClient()
        ).run(
            workload,
            model="test-model",
        )
    )

    assert (
        run.aggregate[
            "total_requests"
        ]
        == 2
    )

    errors = [
        request.error
        for request in run.requests
        if not request.success
    ]

    assert (
        run.aggregate[
            "successful_requests"
        ]
        == 2
    ), errors

    assert (
        run.aggregate[
            "failed_requests"
        ]
        == 0
    )

    assert (
        run.aggregate[
            "total_input_tokens"
        ]
        == 6
    )

    assert (
        run.aggregate[
            "total_output_tokens"
        ]
        == 4
    )

    assert (
        run.aggregate[
            "total_tokens"
        ]
        == 10
    )

    assert (
        run.aggregate[
            "output_token_throughput_tps"
        ]
        is not None
    )

    assert (
        run.aggregate[
            "total_token_throughput_tps"
        ]
        is not None
    )

    assert all(
        request.input_tokens == 3
        for request in run.requests
    )

    assert all(
        request.output_tokens == 2
        for request in run.requests
    )

    assert all(
        request.total_tokens == 5
        for request in run.requests
    )

    assert all(
        request.model == "test-model"
        for request in run.requests
    )


def test_benchmark_records_request_failure() -> None:
    class FailingClient:
        async def achat(
            self,
            **kwargs,
        ):
            raise RuntimeError(
                "simulated failure"
            )

    workload = WorkloadSpec(
        prompts=["a"],
        concurrency=1,
        max_tokens=4,
        temperature=0.0,
        stream=False,
        enable_thinking=False,
    )

    run = asyncio.run(
        AsyncBenchmarkRunner(
            FailingClient()
        ).run(
            workload,
            model="test-model",
        )
    )

    assert (
        run.aggregate[
            "total_requests"
        ]
        == 1
    )

    assert (
        run.aggregate[
            "successful_requests"
        ]
        == 0
    )

    assert (
        run.aggregate[
            "failed_requests"
        ]
        == 1
    )

    request = run.requests[0]

    assert request.success is False
    assert request.error is not None

    assert (
        "RuntimeError"
        in request.error
    )

    assert (
        "simulated failure"
        in request.error
    )


def test_benchmark_preserves_thinking_configuration() -> None:
    class ThinkingClient:
        async def achat(
            self,
            **kwargs,
        ):
            assert (
                kwargs[
                    "chat_template_kwargs"
                ]
                == {
                    "enable_thinking":
                        True,
                }
            )

            return ChatResponse(
                text="answer",
                model="test-model",
                finish_reason="stop",
                usage=TokenUsage(
                    prompt_tokens=2,
                    completion_tokens=3,
                    total_tokens=5,
                ),
            )

    workload = WorkloadSpec(
        prompts=[
            "reason about this"
        ],
        concurrency=1,
        max_tokens=32,
        temperature=0.6,
        stream=False,
        enable_thinking=True,
    )

    run = asyncio.run(
        AsyncBenchmarkRunner(
            ThinkingClient()
        ).run(
            workload,
            model="test-model",
        )
    )

    assert (
        run.aggregate[
            "successful_requests"
        ]
        == 1
    )

    assert (
        run.parameters[
            "enable_thinking"
        ]
        is True
    )


def test_aggregate_accepts_monotonic_elapsed_override() -> None:
    now = datetime.now(UTC)

    request = RequestMeasurement(
        request_id="instant",
        prompt="x",
        started_at=now,
        finished_at=now,
        success=True,
        input_tokens=1,
        output_tokens=2,
        total_tokens=3,
    )

    run = (
        EvidenceBundle
        .with_aggregate(
            run_id="run-instant",
            backend=(
                "nebius-token-factory"
            ),
            model="test-model",
            created_at=now,
            completed_at=now,
            parameters={},
            workload={},
            requests=[request],
            elapsed_s=0.001,
        )
    )

    assert (
        run.aggregate[
            "elapsed_s"
        ]
        == 0.001
    )

    assert (
        run.aggregate[
            "total_input_tokens"
        ]
        == 1
    )

    assert (
        run.aggregate[
            "total_output_tokens"
        ]
        == 2
    )

    assert (
        run.aggregate[
            "total_tokens"
        ]
        == 3
    )

    assert (
        run.aggregate[
            "output_token_throughput_tps"
        ]
        == 2000.0
    )

    assert (
        run.aggregate[
            "total_token_throughput_tps"
        ]
        == 3000.0
    )


def test_aggregate_derives_total_when_combined_usage_is_missing() -> None:
    now = datetime.now(UTC)

    request = RequestMeasurement(
        request_id="derived-total",
        prompt="x",
        started_at=now,
        finished_at=now,
        success=True,
        input_tokens=4,
        output_tokens=6,
        total_tokens=None,
    )

    run = (
        EvidenceBundle
        .with_aggregate(
            run_id="run-derived",
            backend=(
                "nebius-token-factory"
            ),
            model="test-model",
            created_at=now,
            completed_at=now,
            parameters={},
            workload={},
            requests=[request],
            elapsed_s=1.0,
        )
    )

    assert (
        run.aggregate[
            "total_tokens"
        ]
        == 10
    )

    assert (
        run.aggregate[
            "total_token_throughput_tps"
        ]
        == 10.0
    )