"""Explicitly opted-in, credit-consuming Token Factory workflow regression."""

import asyncio
import os

import pytest

from inferdoc import NebiusClient, run_closed_loop
from inferdoc.benchmark.workload import WorkloadSpec
from inferdoc.config import InferDocSettings
from inferdoc.storage import ArtifactStore
from inferdoc.verification import VerificationStatus


@pytest.mark.integration
def test_live_closed_loop(tmp_path) -> None:
    if os.getenv("INFERDOC_RUN_LIVE_TESTS") != "1":
        pytest.skip("set INFERDOC_RUN_LIVE_TESTS=1 to spend Nebius credits")
    settings = InferDocSettings.from_env()
    if not settings.api_key:
        pytest.skip("NEBIUS_API_KEY is required for the opt-in live test")

    async def execute():
        client = NebiusClient(settings=settings)
        try:
            return await run_closed_loop(
                client=client,
                workload=WorkloadSpec(
                    prompts=["Define TTFT in one sentence.",
                             "Define throughput in one sentence."],
                    concurrency=1,
                    max_tokens=32,
                    stream=False,
                    enable_thinking=False,
                ),
                model=settings.default_model,
                artifact_store=ArtifactStore(tmp_path),
            )
        finally:
            await client.aclose()

    result = asyncio.run(execute())
    assert result.baseline.run_id
    assert result.baseline.aggregate["total_requests"] == 2
    assert (tmp_path / result.baseline.run_id / "manifest.json").exists()
    assert result.diagnosis.recommendation_summary
    if result.diagnosis.experiment is None:
        assert result.candidate is None
        assert result.verification is None
        return
    assert result.admission is not None
    if not result.admission.approved:
        assert result.candidate is None
        assert result.verification is None
        return
    assert result.candidate is not None
    assert result.verification is not None
    assert result.verification.status in {
        VerificationStatus.PASS,
        VerificationStatus.FAIL,
        VerificationStatus.INCONCLUSIVE,
    }
    assert result.verification.baseline_run_id == result.baseline.run_id
    assert result.verification.candidate_run_id == result.candidate.run_id
    assert ArtifactStore(tmp_path).verify_manifest(result.candidate.run_id).valid
