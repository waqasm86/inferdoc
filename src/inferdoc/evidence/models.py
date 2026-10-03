from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from ..benchmark.metrics import summary


class RequestMeasurement(BaseModel):
    model_config = ConfigDict(extra="forbid")

    request_id: str
    prompt: str | None = None
    prompt_sha256: str | None = None
    prompt_length: int | None = Field(
        default=None,
        ge=0,
    )

    started_at: datetime
    first_response_at: datetime | None = None
    finished_at: datetime

    success: bool
    error: str | None = None

    input_tokens: int | None = Field(
        default=None,
        ge=0,
    )
    output_tokens: int | None = Field(
        default=None,
        ge=0,
    )
    total_tokens: int | None = Field(
        default=None,
        ge=0,
    )

    model: str | None = None

    @property
    def e2e_latency_s(self) -> float:
        return (
            self.finished_at
            - self.started_at
        ).total_seconds()

    @property
    def ttft_s(self) -> float | None:
        if self.first_response_at is None:
            return None

        return (
            self.first_response_at
            - self.started_at
        ).total_seconds()


class EvidenceCapabilities(BaseModel):
    """Backend support and values actually observed in this run are separate."""

    supports_latency: bool = True
    latency_available: bool = False
    supports_ttft: bool = True
    ttft_available: bool = False
    supports_request_throughput: bool = True
    request_throughput_available: bool = False
    supports_output_token_throughput: bool = True
    output_token_throughput_available: bool = False
    supports_total_token_throughput: bool = True
    total_token_throughput_available: bool = False
    supports_token_usage: bool = True
    token_usage_available: bool = False
    supports_gpu_utilization: bool = False
    gpu_utilization_available: bool = False
    supports_kv_cache_metrics: bool = False
    kv_cache_metrics_available: bool = False


class EvidenceBundle(BaseModel):
    model_config = ConfigDict(extra="forbid")

    schema_version: str = "1.0"

    run_id: str
    backend: str = "nebius-token-factory"
    model: str

    created_at: datetime
    completed_at: datetime

    parameters: dict[str, Any] = Field(
        default_factory=dict
    )

    workload: dict[str, Any] = Field(
        default_factory=dict
    )

    requests: list[RequestMeasurement]

    capabilities: EvidenceCapabilities = Field(default_factory=EvidenceCapabilities)

    provenance: dict[str, Any] = Field(
        default_factory=dict
    )

    aggregate: dict[str, Any] = Field(
        default_factory=dict
    )

    @classmethod
    def with_aggregate(
        cls,
        **kwargs: Any,
    ) -> EvidenceBundle:
        requests: list[
            RequestMeasurement
        ] = kwargs["requests"]

        elapsed_override = kwargs.pop(
            "elapsed_s",
            None,
        )

        wall_elapsed = max(
            (
                kwargs["completed_at"]
                - kwargs["created_at"]
            ).total_seconds(),
            0.0,
        )

        elapsed = (
            float(elapsed_override)
            if elapsed_override is not None
            else wall_elapsed
        )

        successful = [
            request
            for request in requests
            if request.success
        ]

        e2e = [
            request.e2e_latency_s
            for request in successful
        ]

        streaming = kwargs.get("workload", {}).get(
            "stream", kwargs.get("parameters", {}).get("stream", False)
        )
        ttft = [
            request.ttft_s
            for request in successful
            if streaming and request.ttft_s is not None
        ]

        input_values = [
            request.input_tokens
            for request in successful
        ]

        output_values = [
            request.output_tokens
            for request in successful
        ]

        total_values = [
            request.total_tokens
            for request in successful
        ]

        input_complete = (
            bool(successful)
            and all(
                value is not None
                for value in input_values
            )
        )

        output_complete = (
            bool(successful)
            and all(
                value is not None
                for value in output_values
            )
        )

        total_complete = (
            bool(successful)
            and all(
                value is not None
                for value in total_values
            )
        )

        total_input_tokens = (
            sum(
                value
                for value in input_values
                if value is not None
            )
            if input_complete
            else None
        )

        total_output_tokens = (
            sum(
                value
                for value in output_values
                if value is not None
            )
            if output_complete
            else None
        )

        if total_complete:
            total_tokens = sum(
                value
                for value in total_values
                if value is not None
            )

        elif (
            total_input_tokens is not None
            and total_output_tokens is not None
        ):
            # Deterministic fallback when the provider
            # gives complete input/output usage but does
            # not expose a separate combined total.
            total_tokens = (
                total_input_tokens
                + total_output_tokens
            )

        else:
            total_tokens = None

        aggregate = {
            "total_requests":
                len(requests),

            "successful_requests":
                len(successful),

            "failed_requests":
                len(requests)
                - len(successful),

            "success_rate":
                (
                    len(successful)
                    / len(requests)
                    if requests
                    else None
                ),

            "request_throughput_rps":
                (
                    len(successful)
                    / elapsed
                    if elapsed > 0
                    else None
                ),

            "output_token_throughput_tps":
                (
                    total_output_tokens
                    / elapsed
                    if (
                        total_output_tokens
                        is not None
                        and elapsed > 0
                    )
                    else None
                ),

            "total_token_throughput_tps":
                (
                    total_tokens
                    / elapsed
                    if (
                        total_tokens
                        is not None
                        and elapsed > 0
                    )
                    else None
                ),

            "latency_s":
                summary(e2e),

            "ttft_s":
                summary(ttft),

            "total_input_tokens":
                total_input_tokens,

            "total_output_tokens":
                total_output_tokens,

            "total_tokens":
                total_tokens,

            "elapsed_s":
                elapsed,
        }

        # This describes measured availability, not backend admission policy.
        kwargs.pop("capabilities", None)
        capabilities = EvidenceCapabilities(
            latency_available=aggregate["latency_s"]["mean"] is not None,
            ttft_available=bool(streaming) and aggregate["ttft_s"]["mean"] is not None,
            request_throughput_available=aggregate["request_throughput_rps"] is not None,
            output_token_throughput_available=aggregate["output_token_throughput_tps"] is not None,
            total_token_throughput_available=aggregate["total_token_throughput_tps"] is not None,
            token_usage_available=(
                total_input_tokens is not None
                and total_output_tokens is not None
                and total_tokens is not None
            ),
        )
        return cls(
            aggregate=aggregate,
            capabilities=capabilities,
            **kwargs,
        )
