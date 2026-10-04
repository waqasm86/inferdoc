import pytest

from inferdoc.experiments.capabilities import TOKEN_FACTORY_CAPABILITIES
from inferdoc.experiments.models import Constraint, ExperimentSpec, MetricDirection, MetricRule
from inferdoc.experiments.policy import validate_experiment
from inferdoc.verification.verifier import VerificationStatus, verify


def experiment(baseline_id: str, changed: dict) -> ExperimentSpec:
    return ExperimentSpec(
        id="exp-1",
        hypothesis="More client concurrency increases output throughput.",
        model="nvidia/NVIDIA-Nemotron-3-Nano-30B-A3B",
        baseline_run_id=baseline_id,
        changed_variables=changed,
        controlled_variables={"max_tokens": 16, "temperature": 0.0, "stream": False},
        objective="increase throughput",
        verification_metrics=[
            MetricRule(
                metric="output_token_throughput_tps",
                direction=MetricDirection.MAXIMIZE,
                minimum_relative_change=0.05,
            )
        ],
        constraints=[Constraint(metric="latency_s.p95", maximum=3.0)],
        rationale="controlled concurrency experiment",
    )


def test_policy_rejects_unavailable_server_control(evidence) -> None:
    decision = validate_experiment(
        experiment(evidence.run_id, {"tensor_parallel_size": 2}),
        TOKEN_FACTORY_CAPABILITIES,
        baseline=evidence,
    )
    assert not decision.approved
    assert "tensor_parallel_size" in " ".join(decision.reasons)


def test_verification_pass_fail_and_inconclusive(evidence) -> None:
    exp = experiment(evidence.run_id, {"concurrency": 2})
    candidate = evidence.model_copy(deep=True)
    candidate.run_id = "run-candidate"
    candidate.workload["concurrency"] = 2
    candidate.aggregate["output_token_throughput_tps"] = (
        evidence.aggregate["output_token_throughput_tps"] * 2
    )
    assert (
        verify(baseline=evidence, candidate=candidate, experiment=exp).status
        == VerificationStatus.PASS
    )
    candidate.aggregate["output_token_throughput_tps"] = 0.01
    assert (
        verify(baseline=evidence, candidate=candidate, experiment=exp).status
        == VerificationStatus.FAIL
    )
    candidate.aggregate["output_token_throughput_tps"] = None
    assert (
        verify(baseline=evidence, candidate=candidate, experiment=exp).status
        == VerificationStatus.INCONCLUSIVE
    )


def test_verification_detects_wrong_baseline(evidence) -> None:
    exp = experiment("other-run", {"concurrency": 2})
    candidate = evidence.model_copy(deep=True)
    candidate.run_id = "run-candidate"
    report = verify(baseline=evidence, candidate=candidate, experiment=exp)
    assert report.status == VerificationStatus.FAIL


def test_policy_accepts_nested_observable_metric(evidence) -> None:
    decision = validate_experiment(
        experiment(evidence.run_id, {"concurrency": 2}),
        TOKEN_FACTORY_CAPABILITIES,
        baseline=evidence,
    )
    assert decision.approved


def test_policy_rejects_unobservable_constraint(evidence) -> None:
    exp = experiment(evidence.run_id, {"concurrency": 2})
    exp.constraints = [Constraint(metric="gpu_utilization.p95", maximum=95.0)]
    decision = validate_experiment(exp, TOKEN_FACTORY_CAPABILITIES, baseline=evidence)
    assert not decision.approved
    assert "gpu_utilization.p95" in " ".join(decision.reasons)


def test_policy_can_limit_experiment_to_one_changed_variable(evidence) -> None:
    decision = validate_experiment(
        experiment(evidence.run_id, {"concurrency": 2, "max_tokens": 32}),
        TOKEN_FACTORY_CAPABILITIES,
        baseline=evidence,
        max_changed_variables=1,
    )
    assert not decision.approved
    assert "policy limit is 1" in " ".join(decision.reasons)


@pytest.mark.parametrize(
    "changed",
    [
        {"concurrency": "two"},
        {"concurrency": True},
        {"max_tokens": 1.5},
        {"temperature": float("nan")},
        {"temperature": 10**1000},
        {"stream": "true"},
        {"prompts": []},
        {"prompts": ["ok", " "]},
    ],
)
def test_policy_rejects_invalid_control_values_before_rerun(evidence, changed) -> None:
    decision = validate_experiment(
        experiment(evidence.run_id, changed),
        TOKEN_FACTORY_CAPABILITIES,
        baseline=evidence,
    )
    assert not decision.approved
    assert decision.reasons
