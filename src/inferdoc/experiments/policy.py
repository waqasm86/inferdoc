from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field

from .models import ExperimentSpec


def _metric_root(path: str) -> str:
    """Return the top-level evidence field referenced by a metric path.

    Examples:
        "latency_s.p95" -> "latency_s"
        "ttft_s.p95" -> "ttft_s"
        "request_throughput_rps" -> "request_throughput_rps"
    """
    return path.split(".", 1)[0]


class BackendCapabilities(BaseModel):
    """Controls and measurements exposed by an inference backend."""

    backend: str
    controllable_fields: set[str] = Field(default_factory=set)
    observable_fields: set[str] = Field(default_factory=set)
    domains: dict[str, tuple[float, float]] = Field(default_factory=dict)


class AdmissionDecision(BaseModel):
    """Deterministic result of validating a proposed experiment."""

    approved: bool
    reasons: list[str] = Field(default_factory=list)
    experiment_id: str


def validate_experiment(
    experiment: ExperimentSpec,
    capabilities: BackendCapabilities,
    *,
    baseline: Any | None = None,
    max_requests: int = 64,
    max_changed_variables: int | None = None,
) -> AdmissionDecision:
    """Validate an ExperimentSpec against backend capabilities and policy.

    Nemotron may propose an experiment, but deterministic Python code decides
    whether the experiment is executable and whether its requested evidence
    can actually be observed by the selected backend.
    """
    reasons: list[str] = []

    if (
        max_changed_variables is not None
        and len(experiment.changed_variables) > max_changed_variables
    ):
        reasons.append(
            f"experiment changes {len(experiment.changed_variables)} variables; "
            f"policy limit is {max_changed_variables}"
        )

    # The experiment must target the backend represented by the supplied
    # capability declaration.
    if experiment.backend != capabilities.backend:
        reasons.append(
            f"backend {experiment.backend!r} is not {capabilities.backend!r}"
        )

    # Every changed variable must be an exposed backend control.
    # Numeric controls must also remain inside their declared domains.
    for name, value in experiment.changed_variables.items():
        if name not in capabilities.controllable_fields:
            reasons.append(
                f"{name} is not an exposed control for this backend"
            )

        if name in capabilities.domains and isinstance(value, (int, float)):
            low, high = capabilities.domains[name]

            if not low <= value <= high:
                reasons.append(
                    f"{name}={value!r} is outside allowed range "
                    f"[{low}, {high}]"
                )

    # Closed-loop verification requires measured baseline evidence.
    if baseline is None:
        reasons.append("baseline evidence is required")

    # Verification metrics may use nested metric paths such as
    # "latency_s.p95". Backend capability checking is performed against
    # the top-level evidence field: "latency_s".
    for rule in experiment.verification_metrics:
        metric_name = _metric_root(rule.metric)

        if metric_name not in capabilities.observable_fields:
            reasons.append(
                f"verification metric {rule.metric!r} "
                "is not observable on this backend"
            )

    # Constraints must also reference evidence that the backend can observe.
    # This prevents Nemotron from proposing deterministic acceptance criteria
    # based on unavailable telemetry such as GPU utilization.
    for rule in experiment.constraints:
        metric_name = _metric_root(rule.metric)

        if metric_name not in capabilities.observable_fields:
            reasons.append(
                f"constraint metric {rule.metric!r} "
                "is not observable on this backend"
            )

    # Bound experiments that replace the prompt workload so an agent cannot
    # accidentally propose an unexpectedly large request set.
    if "prompts" in experiment.changed_variables:
        prompts = experiment.changed_variables["prompts"]

        if isinstance(prompts, list) and len(prompts) > max_requests:
            reasons.append(
                f"experiment requests {len(prompts)} prompts; "
                f"budget limit is {max_requests}"
            )

    # A variable cannot simultaneously be held constant and deliberately
    # changed by the same experiment.
    controlled = set(experiment.controlled_variables)
    changed = set(experiment.changed_variables)
    overlap = sorted(controlled & changed)

    if overlap:
        reasons.append(
            "variables cannot be both changed and controlled: "
            + ", ".join(overlap)
        )

    return AdmissionDecision(
        approved=not reasons,
        reasons=reasons,
        experiment_id=experiment.id,
    )
