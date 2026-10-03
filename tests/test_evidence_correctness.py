import asyncio
import inspect

import pytest

from inferdoc.benchmark.runner import AsyncBenchmarkRunner, benchmark
from inferdoc.benchmark.workload import WorkloadSpec
from inferdoc.cli import _parser, main
from inferdoc.evidence.models import EvidenceBundle
from inferdoc.nebius.models import ChatResponse, TokenUsage
from inferdoc.verification import VerificationStatus, compare_workloads, verify
from test_policy_verification import experiment


def test_nonstreaming_defaults_and_cli_flag(monkeypatch, tmp_path, evidence, capsys):
    assert WorkloadSpec(prompts=["one"]).stream is False
    assert inspect.signature(benchmark).parameters["stream"].default is False
    assert _parser().parse_args(["bench", "one"]).stream is False
    assert _parser().parse_args(["bench", "--stream", "one"]).stream is True
    with pytest.raises(SystemExit):
        _parser().parse_args(["bench", "--no-stream", "one"])

    seen = []
    monkeypatch.setattr("inferdoc.cli.benchmark", lambda **kw: (seen.append(kw), evidence)[1])
    main(["bench", "--artifact-dir", str(tmp_path), "one"])
    main(["bench", "--artifact-dir", str(tmp_path), "--stream", "one"])
    assert [call["stream"] for call in seen] == [False, True]
    capsys.readouterr()


def test_run_capabilities_nonstreaming_and_streaming():
    class Client:
        async def achat(self, **kwargs):
            if kwargs["stream"]:
                async def chunks():
                    yield "hello"
                return chunks()
            return ChatResponse(
                text="hello", model="test", finish_reason="stop",
                usage=TokenUsage(prompt_tokens=2, completion_tokens=3, total_tokens=5),
            )

    async def run(stream):
        return await AsyncBenchmarkRunner(Client()).run(
            WorkloadSpec(prompts=["one"], stream=stream), model="test"
        )

    regular = asyncio.run(run(False))
    streamed = asyncio.run(run(True))
    assert regular.capabilities.latency_available
    assert regular.capabilities.request_throughput_available
    assert regular.capabilities.token_usage_available
    assert regular.capabilities.output_token_throughput_available
    assert regular.capabilities.total_token_throughput_available
    assert not regular.capabilities.ttft_available
    assert regular.aggregate["ttft_s"]["mean"] is None
    assert streamed.capabilities.ttft_available
    assert not streamed.capabilities.token_usage_available
    assert not streamed.capabilities.output_token_throughput_available
    assert not streamed.capabilities.total_token_throughput_available
    assert streamed.aggregate["total_tokens"] is None
    for run in (regular, streamed):
        assert not run.capabilities.supports_gpu_utilization
        assert not run.capabilities.gpu_utilization_available
        assert not run.capabilities.supports_kv_cache_metrics
        assert not run.capabilities.kv_cache_metrics_available


def test_incomplete_usage_is_unavailable(evidence):
    requests = [request.model_copy(deep=True) for request in evidence.requests]
    requests[1].output_tokens = None
    requests[1].total_tokens = None
    run = EvidenceBundle.with_aggregate(
        **evidence.model_dump(exclude={"aggregate", "capabilities", "requests"}),
        requests=requests,
    )
    assert not run.capabilities.token_usage_available
    assert not run.capabilities.output_token_throughput_available
    assert not run.capabilities.total_token_throughput_available


@pytest.mark.parametrize("field,value", [
    ("prompts", ["two", "one"]),
    ("max_tokens", 32),
    ("temperature", 0.7),
    ("enable_thinking", True),
    ("stream", True),
])
def test_uncontrolled_drift_fails(evidence, field, value):
    exp = experiment(evidence.run_id, {"concurrency": 2})
    candidate = evidence.model_copy(deep=True)
    candidate.run_id = "candidate"
    candidate.workload["concurrency"] = 2
    candidate.workload[field] = value
    assert compare_workloads(evidence, candidate, exp).mismatches
    assert verify(baseline=evidence, candidate=candidate, experiment=exp).status == VerificationStatus.FAIL


def test_intended_change_and_invalid_candidate(evidence):
    exp = experiment(evidence.run_id, {"concurrency": 2})
    candidate = evidence.model_copy(deep=True)
    candidate.run_id = "candidate"
    candidate.workload["concurrency"] = 2
    candidate.aggregate["output_token_throughput_tps"] *= 2
    assert compare_workloads(evidence, candidate, exp).comparable
    assert verify(baseline=evidence, candidate=candidate, experiment=exp).status == VerificationStatus.PASS
    candidate.workload["concurrency"] = 3
    assert verify(baseline=evidence, candidate=candidate, experiment=exp).status == VerificationStatus.FAIL


def test_request_prompt_order_must_match_declared_workload(evidence):
    exp = experiment(evidence.run_id, {"concurrency": 2})
    candidate = evidence.model_copy(deep=True)
    candidate.run_id = "candidate"
    candidate.workload["concurrency"] = 2
    candidate.requests.reverse()
    assert verify(baseline=evidence, candidate=candidate, experiment=exp).status == VerificationStatus.FAIL


@pytest.mark.parametrize("field", ["backend", "model"])
def test_identity_mismatch_fails(evidence, field):
    exp = experiment(evidence.run_id, {"concurrency": 2})
    candidate = evidence.model_copy(deep=True)
    candidate.run_id = "candidate"
    candidate.workload["concurrency"] = 2
    setattr(candidate, field, "other")
    assert verify(baseline=evidence, candidate=candidate, experiment=exp).status == VerificationStatus.FAIL


def test_missing_metric_and_objective_miss(evidence):
    exp = experiment(evidence.run_id, {"concurrency": 2})
    candidate = evidence.model_copy(deep=True)
    candidate.run_id = "candidate"
    candidate.workload["concurrency"] = 2
    candidate.aggregate["output_token_throughput_tps"] = None
    assert verify(baseline=evidence, candidate=candidate, experiment=exp).status == VerificationStatus.INCONCLUSIVE
    candidate.aggregate["output_token_throughput_tps"] = 0.01
    assert verify(baseline=evidence, candidate=candidate, experiment=exp).status == VerificationStatus.FAIL
