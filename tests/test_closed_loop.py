import asyncio

import pytest

from inferdoc.benchmark.workload import WorkloadSpec
from inferdoc.doctor.models import DiagnosisReport
from inferdoc.storage import ArtifactStore
from inferdoc.verification import VerificationStatus
from inferdoc.workflows import run_closed_loop
from test_policy_verification import experiment


@pytest.mark.parametrize("concurrency,expected_candidate", [(2, True), (100, False), (None, False)])
def test_reusable_workflow(monkeypatch, tmp_path, evidence, concurrency, expected_candidate):
    calls = []

    async def baseline_run(self, workload, *, model=None):
        calls.append("baseline")
        return evidence.model_copy(deep=True)

    async def diagnose(self, baseline):
        calls.append("diagnose")
        exp = experiment(baseline.run_id, {"concurrency": concurrency}) if concurrency else None
        return DiagnosisReport(recommendation_summary="test", experiment=exp)

    async def rerun(exp, **kwargs):
        calls.append("rerun")
        candidate = evidence.model_copy(deep=True)
        candidate.run_id = "candidate"
        candidate.workload["concurrency"] = concurrency
        candidate.aggregate["output_token_throughput_tps"] *= 2
        return candidate

    monkeypatch.setattr("inferdoc.workflows.closed_loop.AsyncBenchmarkRunner.run", baseline_run)
    monkeypatch.setattr("inferdoc.workflows.closed_loop.DoctorAgent.adiagnose", diagnose)
    monkeypatch.setattr("inferdoc.workflows.closed_loop.run_experiment", rerun)
    store = ArtifactStore(tmp_path)
    result = asyncio.run(run_closed_loop(
        client=object(), workload=WorkloadSpec(prompts=["one", "two"]),
        model=evidence.model, artifact_store=store,
    ))
    assert calls[:2] == ["baseline", "diagnose"]
    assert (tmp_path / evidence.run_id / "evidence.json").exists()
    assert (tmp_path / evidence.run_id / "diagnosis.json").exists()
    assert (result.candidate is not None) is expected_candidate
    if expected_candidate:
        assert result.admission.approved
        assert result.verification.status == VerificationStatus.PASS
        assert (tmp_path / evidence.run_id / "experiment.json").exists()
        assert (tmp_path / "candidate" / "verification.json").exists()
        assert calls[-1] == "rerun"
    elif concurrency:
        assert result.admission is not None and not result.admission.approved
        assert "rerun" not in calls
    else:
        assert result.admission is None
        assert "rerun" not in calls
