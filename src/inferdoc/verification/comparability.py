"""Deterministic workload comparison for controlled experiments."""

from __future__ import annotations

from pydantic import BaseModel, Field

from ..benchmark.workload import WorkloadSpec
from ..evidence.models import EvidenceBundle
from ..evidence.provenance import canonical_sha256
from ..experiments.models import ExperimentSpec


class ComparabilityReport(BaseModel):
    mismatches: list[str] = Field(default_factory=list)
    missing: list[str] = Field(default_factory=list)

    @property
    def comparable(self) -> bool:
        return not self.mismatches and not self.missing


def _prompt_hashes(bundle: EvidenceBundle) -> list[str] | None:
    prompts = bundle.workload.get("prompts")
    if isinstance(prompts, list) and prompts:
        return [canonical_sha256(prompt) for prompt in prompts]
    saved = bundle.workload.get("prompt_sha256")
    if isinstance(saved, list) and saved:
        return saved
    if bundle.requests and all(r.prompt_sha256 or r.prompt for r in bundle.requests):
        return [r.prompt_sha256 or canonical_sha256(r.prompt) for r in bundle.requests]
    return None


def _value(bundle: EvidenceBundle, field: str):
    if field == "prompts":
        return _prompt_hashes(bundle)
    if field in bundle.workload:
        return bundle.workload[field]
    if field in bundle.parameters:
        return bundle.parameters[field]
    # Older evidence omitted default fields; the workload schema supplies them.
    if field in WorkloadSpec.model_fields:
        return WorkloadSpec.model_fields[field].default
    return None


def compare_workloads(
    baseline: EvidenceBundle,
    candidate: EvidenceBundle,
    experiment: ExperimentSpec,
) -> ComparabilityReport:
    report = ComparabilityReport()
    for name in ("backend", "model"):
        actual = getattr(baseline, name)
        if actual != getattr(candidate, name) or actual != getattr(experiment, name):
            report.mismatches.append(f"{name} identity differs")
    if experiment.baseline_run_id != baseline.run_id:
        report.mismatches.append("experiment baseline_run_id does not identify baseline")

    for label, bundle in (("baseline", baseline), ("candidate", candidate)):
        declared = _prompt_hashes(bundle)
        observed = [r.prompt_sha256 or (canonical_sha256(r.prompt) if r.prompt is not None else None)
                    for r in bundle.requests]
        if declared is not None and observed and all(value is not None for value in observed):
            if declared != observed:
                report.mismatches.append(f"{label} request prompts differ from declared workload")

    fields = set(WorkloadSpec.model_fields) | set(experiment.controlled_variables) | set(experiment.changed_variables)
    for name in sorted(fields):
        before, after = _value(baseline, name), _value(candidate, name)
        if before is None or after is None:
            report.missing.append(f"workload field {name!r} is missing")
            continue
        if name in experiment.changed_variables:
            expected = experiment.changed_variables[name]
            if name == "prompts":
                expected = [canonical_sha256(prompt) for prompt in expected]
            if after != expected:
                report.mismatches.append(f"candidate did not apply changed variable {name!r}")
        elif name in experiment.controlled_variables:
            expected = experiment.controlled_variables[name]
            if name == "prompts":
                expected = [canonical_sha256(prompt) for prompt in expected]
            if before != expected or after != expected:
                report.mismatches.append(f"controlled variable {name!r} was not held at its expected value")
        elif before != after:
            report.mismatches.append(f"uncontrolled workload drift in {name!r}")
    return report
