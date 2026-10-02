from datetime import UTC, datetime, timedelta

import pytest

from inferdoc.evidence.models import EvidenceBundle, RequestMeasurement


@pytest.fixture
def evidence() -> EvidenceBundle:
    start = datetime(2026, 1, 1, tzinfo=UTC)
    requests = [
        RequestMeasurement(
            request_id="r1",
            prompt="one",
            started_at=start,
            first_response_at=start + timedelta(seconds=0.1),
            finished_at=start + timedelta(seconds=1),
            success=True,
            input_tokens=4,
            output_tokens=8,
            total_tokens=12,
        ),
        RequestMeasurement(
            request_id="r2",
            prompt="two",
            started_at=start + timedelta(seconds=0.1),
            first_response_at=start + timedelta(seconds=0.2),
            finished_at=start + timedelta(seconds=2),
            success=True,
            input_tokens=5,
            output_tokens=10,
            total_tokens=15,
        ),
    ]
    return EvidenceBundle.with_aggregate(
        run_id="run-baseline",
        backend="nebius-token-factory",
        model="nvidia/NVIDIA-Nemotron-3-Nano-30B-A3B",
        created_at=start,
        completed_at=start + timedelta(seconds=2),
        parameters={"stream": False},
        workload={
            "prompts": ["one", "two"],
            "concurrency": 1,
            "max_tokens": 16,
            "temperature": 0.0,
            "stream": False,
        },
        requests=requests,
    )
