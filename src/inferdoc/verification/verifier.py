from __future__ import annotations

from enum import StrEnum
from typing import Any

from pydantic import BaseModel, Field

from ..evidence.models import EvidenceBundle
from ..experiments.models import Constraint, ExperimentSpec, MetricDirection, MetricRule
from .comparability import compare_workloads


class VerificationStatus(StrEnum):
    PASS = "PASS"
    FAIL = "FAIL"
    INCONCLUSIVE = "INCONCLUSIVE"


class MetricEvaluation(BaseModel):
    metric: str
    baseline: float | None
    candidate: float | None
    relative_change: float | None
    passed: bool | None
    reason: str


class ConstraintEvaluation(BaseModel):
    metric: str
    value: float | None
    passed: bool | None
    reason: str


class VerificationReport(BaseModel):
    status: VerificationStatus
    baseline_run_id: str
    candidate_run_id: str
    experiment_id: str
    metric_results: list[MetricEvaluation] = Field(default_factory=list)
    constraint_results: list[ConstraintEvaluation] = Field(default_factory=list)
    reasons: list[str] = Field(default_factory=list)


def _metric(bundle: EvidenceBundle, name: str) -> float | None:
    value: Any = bundle.aggregate
    for part in name.split("."):
        if isinstance(value, dict):
            value = value.get(part)
        else:
            return None
    return float(value) if isinstance(value, (int, float)) else None


def _rule(rule: MetricRule, baseline: float | None, candidate: float | None) -> MetricEvaluation:
    if baseline is None or candidate is None:
        return MetricEvaluation(
            metric=rule.metric,
            baseline=baseline,
            candidate=candidate,
            relative_change=None,
            passed=None,
            reason="required metric is missing",
        )
    relative = (candidate - baseline) / abs(baseline) if baseline else None
    if relative is None:
        return MetricEvaluation(
            metric=rule.metric,
            baseline=baseline,
            candidate=candidate,
            relative_change=None,
            passed=None,
            reason="baseline is zero; relative comparison is undefined",
        )
    if rule.direction == MetricDirection.MAXIMIZE:
        passed = relative >= rule.minimum_relative_change
    else:
        passed = relative <= -rule.minimum_relative_change
    return MetricEvaluation(
        metric=rule.metric,
        baseline=baseline,
        candidate=candidate,
        relative_change=relative,
        passed=passed,
        reason="threshold met" if passed else "objective threshold not met",
    )


def _constraint(rule: Constraint, candidate: float | None) -> ConstraintEvaluation:
    if candidate is None:
        return ConstraintEvaluation(
            metric=rule.metric,
            value=None,
            passed=None,
            reason="required constraint metric is missing",
        )
    passed = True
    if rule.maximum is not None:
        passed = candidate <= rule.maximum
    if rule.minimum is not None:
        passed = candidate >= rule.minimum
    return ConstraintEvaluation(
        metric=rule.metric,
        value=candidate,
        passed=passed,
        reason="constraint met" if passed else "constraint violated",
    )


def verify(
    *, baseline: EvidenceBundle, candidate: EvidenceBundle, experiment: ExperimentSpec
) -> VerificationReport:
    comparison = compare_workloads(baseline, candidate, experiment)
    reasons = [*comparison.mismatches, *comparison.missing]
    metric_results = [
        _rule(r, _metric(baseline, r.metric), _metric(candidate, r.metric))
        for r in experiment.verification_metrics
    ]
    constraint_results = [
        _constraint(r, _metric(candidate, r.metric)) for r in experiment.constraints
    ]
    if comparison.mismatches:
        status = VerificationStatus.FAIL
    elif comparison.missing or any(x.passed is None for x in [*metric_results, *constraint_results]):
        status = VerificationStatus.INCONCLUSIVE
        reasons.append("required evidence is missing")
    elif not all(x.passed for x in [*metric_results, *constraint_results]):
        status = VerificationStatus.FAIL
    else:
        status = VerificationStatus.PASS
    return VerificationReport(
        status=status,
        baseline_run_id=baseline.run_id,
        candidate_run_id=candidate.run_id,
        experiment_id=experiment.id,
        metric_results=metric_results,
        constraint_results=constraint_results,
        reasons=reasons,
    )
