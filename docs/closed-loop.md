# Closed-loop workflow

`run_closed_loop` composes baseline benchmark → Nemotron diagnosis → deterministic experiment admission → candidate rerun → Python verification. It writes local artifacts throughout. The default `DEMO_TOKEN_FACTORY_CAPABILITIES` allows one changed client concurrency value in 1–8; other workload fields stay controlled. A Doctor report with no executable proposal, or a rejected proposal, is a valid workflow result with no candidate or verification.

```python
import asyncio
from inferdoc import InferDocSettings, NebiusClient, run_closed_loop
from inferdoc.benchmark import WorkloadSpec
from inferdoc.storage import ArtifactStore

async def main():
    settings = InferDocSettings.from_env()
    async with NebiusClient(settings=settings) as client:
        return await run_closed_loop(
            client=client,
            workload=WorkloadSpec(
                prompts=["Define TTFT.", "Define throughput."],
                concurrency=1,
                max_tokens=32,
            ),
            model=settings.default_model,
            artifact_store=ArtifactStore(settings.artifact_dir),
        )

# Live Token Factory/Nemotron calls; requires NEBIUS_API_KEY and spends credits.
result = asyncio.run(main())
print(result.admission, result.verification)
```

The returned `ClosedLoopResult` contains `baseline`, `diagnosis`, and optional `admission`, `candidate`, and `verification`. It raises if the baseline has no successful requests. Python checks proposed controls before a rerun, and `verify` compares the candidate with the declared baseline. Nemotron does not decide PASS/FAIL/INCONCLUSIVE.

CLI equivalent, also live:

```bash
inferdoc closed-loop --prompt "Define TTFT." --prompt "Define throughput." --concurrency 1 --max-tokens 32
```

The CLI defaults to non-streaming and disabled workload-model thinking. It reports run IDs, admission, verification status, and artifact root as JSON. An approved experiment can still yield FAIL or INCONCLUSIVE. See [CLI](cli.md), [diagnosis](diagnosis.md), [experiments](experiments.md), and [verification](verification.md). For a no-credit walkthrough use [offline replay](../examples/05_replay_verification.py).
