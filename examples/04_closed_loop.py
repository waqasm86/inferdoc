"""Run the real InferDoc hackathon closed loop with explicit live opt-in."""

from __future__ import annotations

import asyncio
import os

from dotenv import load_dotenv

from inferdoc import NebiusClient, run_closed_loop
from inferdoc.benchmark import WorkloadSpec
from inferdoc.config import InferDocSettings
from inferdoc.storage import ArtifactStore

PROMPTS = [
    "Explain TTFT in two sentences.",
    "Explain request throughput in two sentences.",
    "Explain token throughput in two sentences.",
    "Explain p95 latency in two sentences.",
    "Explain inference concurrency in two sentences.",
    "Explain streaming inference in two sentences.",
    "Explain the latency versus throughput tradeoff in two sentences.",
    "Explain why benchmarking needs controlled workloads in two sentences.",
]


async def main() -> None:
    load_dotenv()
    settings = InferDocSettings.from_env()
    if not settings.api_key or os.getenv("INFERDOC_RUN_LIVE_TESTS") != "1":
        print("Set NEBIUS_API_KEY and INFERDOC_RUN_LIVE_TESTS=1 for the live demo.")
        return

    client = NebiusClient(settings=settings)
    try:
        result = await run_closed_loop(
            client=client,
            workload=WorkloadSpec(prompts=PROMPTS, concurrency=1, max_tokens=64),
            model=settings.default_model,
            artifact_store=ArtifactStore(settings.artifact_dir),
        )
        print(result.model_dump_json(indent=2, exclude={"baseline": {"requests"}, "candidate": {"requests"}}))
        print("PASS, FAIL, and INCONCLUSIVE are all legitimate measured outcomes.")
    finally:
        await client.aclose()


if __name__ == "__main__":
    asyncio.run(main())
