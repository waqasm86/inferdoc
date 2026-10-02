"""Run the real InferDoc hackathon closed loop."""

from __future__ import annotations

import asyncio
import os

from dotenv import load_dotenv

import inferdoc
from inferdoc.benchmark.workload import WorkloadSpec
from inferdoc.config import InferDocSettings
from inferdoc.doctor.agent import DoctorAgent
from inferdoc.experiments.capabilities import (
    DEMO_TOKEN_FACTORY_CAPABILITIES,
)
from inferdoc.experiments.policy import validate_experiment
from inferdoc.experiments.runner import run_experiment
from inferdoc.storage import ArtifactStore


load_dotenv()


PROMPTS = [
    "Explain TTFT in two sentences.",
    "Explain request throughput in two sentences.",
    "Explain token throughput in two sentences.",
    "Explain p95 latency in two sentences.",
    "Explain inference concurrency in two sentences.",
    "Explain streaming inference in two sentences.",
    (
        "Explain the latency versus throughput "
        "tradeoff in two sentences."
    ),
    (
        "Explain why inference benchmarking "
        "needs controlled workloads in two sentences."
    ),
]


async def main() -> None:
    settings = InferDocSettings.from_env()

    if (
        not settings.api_key
        or os.getenv("INFERDOC_RUN_LIVE_TESTS") != "1"
    ):
        print(
            "Set NEBIUS_API_KEY and "
            "INFERDOC_RUN_LIVE_TESTS=1 "
            "in .env to run the live demo."
        )
        return

    print(
        "InferDoc workload model:",
        settings.default_model,
    )

    print(
        "InferDoc doctor model:",
        settings.doctor_model,
    )

    print(
        "Token Factory endpoint:",
        settings.base_url,
    )

    client = inferdoc.NebiusClient(
        settings=settings,
    )

    store = ArtifactStore()

    try:
        workload = WorkloadSpec(
            prompts=PROMPTS,
            concurrency=1,
            max_tokens=64,
            temperature=0.0,
            stream=False,
            enable_thinking=False,
        )

        print(
            "\n=== BASELINE BENCHMARK ==="
        )

        baseline = await (
            inferdoc.AsyncBenchmarkRunner(
                client,
            ).run(
                workload,
                model=settings.default_model,
            )
        )

        store.save(
            baseline,
        )

        print(
            baseline.model_dump_json(
                indent=2,
                exclude={
                    "requests",
                },
            )
        )

        if (
            baseline.aggregate.get(
                "successful_requests",
            )
            == 0
        ):
            raise RuntimeError(
                "Baseline produced no "
                "successful requests."
            )

        print(
            "\n=== NEMOTRON DIAGNOSIS ==="
        )

        doctor = DoctorAgent(
            client,
            capabilities=(
                DEMO_TOKEN_FACTORY_CAPABILITIES
            ),
        )

        diagnosis = await (
            doctor.adiagnose(
                baseline,
            )
        )

        store.save_diagnosis(
            diagnosis,
            baseline.run_id,
        )

        print(
            diagnosis.model_dump_json(
                indent=2,
            )
        )

        if (
            diagnosis.experiment
            is None
        ):
            print(
                "No executable experiment "
                "was recommended. "
                "This is a valid outcome."
            )
            return

        print(
            "\n=== DETERMINISTIC ADMISSION ==="
        )

        decision = (
            validate_experiment(
                diagnosis.experiment,
                DEMO_TOKEN_FACTORY_CAPABILITIES,
                baseline=baseline,
                max_changed_variables=1,
            )
        )

        print(
            decision.model_dump_json(
                indent=2,
            )
        )

        if not decision.approved:
            print(
                "Experiment rejected by "
                "deterministic policy."
            )
            return

        store.save_experiment(
            diagnosis.experiment,
            baseline.run_id,
        )

        print(
            "\n=== CANDIDATE RERUN ==="
        )

        candidate = await (
            run_experiment(
                diagnosis.experiment,
                client=client,
                baseline=baseline,
                capabilities=(
                    DEMO_TOKEN_FACTORY_CAPABILITIES
                ),
            )
        )

        store.save(
            candidate,
        )

        print(
            candidate.model_dump_json(
                indent=2,
                exclude={
                    "requests",
                },
            )
        )

        print(
            "\n=== DETERMINISTIC VERIFICATION ==="
        )

        verification = inferdoc.verify(
            baseline=baseline,
            candidate=candidate,
            experiment=diagnosis.experiment,
        )

        store.save_verification(
            verification,
            candidate.run_id,
        )

        print(
            verification.model_dump_json(
                indent=2,
            )
        )

        print(
            "\nPASS, FAIL, and INCONCLUSIVE "
            "are all legitimate measured outcomes."
        )

    finally:
        await client.aclose()


if __name__ == "__main__":
    asyncio.run(
        main()
    )