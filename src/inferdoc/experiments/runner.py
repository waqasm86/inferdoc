from __future__ import annotations

from typing import Any

from ..benchmark.runner import AsyncBenchmarkRunner, BenchmarkLimits
from ..benchmark.workload import WorkloadSpec
from ..evidence.models import EvidenceBundle
from .models import ExperimentSpec
from .policy import BackendCapabilities, validate_experiment


async def run_experiment(
    experiment: ExperimentSpec,
    *,
    client: Any,
    baseline: EvidenceBundle,
    capabilities: BackendCapabilities,
    limits: BenchmarkLimits | None = None,
) -> EvidenceBundle:
    decision = validate_experiment(
        experiment,
        capabilities,
        baseline=baseline,
        max_requests=(limits or BenchmarkLimits()).max_requests,
    )
    if not decision.approved:
        raise ValueError("experiment rejected: " + "; ".join(decision.reasons))
    values = dict(baseline.workload)
    values.update(experiment.changed_variables)
    workload = WorkloadSpec.model_validate(values)
    return await AsyncBenchmarkRunner(client, limits=limits).run(workload, model=experiment.model)
