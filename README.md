# InferDoc

**Evidence-driven LLM inference engineering for Nebius Token Factory.** InferDoc measures a hosted workload, asks NVIDIA Nemotron for one bounded experiment, and uses Python to admit and verify the measured rerun.

```text
INFER → MEASURE → ANALYZE → DIAGNOSE → RECOMMEND → VALIDATE → RERUN → VERIFY
```

Nebius Token Factory performs hosted inference. Python owns request timing, success/failure, token accounting when returned, percentiles, throughput, capability admission, workload comparison, thresholds, and `PASS` / `FAIL` / `INCONCLUSIVE`. Nemotron interprets evidence, identifies missing information, and proposes a hypothesis; it does not decide the final status.

Built for the Nebius x NVIDIA Global AI Hackathon, Best Apps and Agents track. The default workload and Doctor model is `nvidia/NVIDIA-Nemotron-3-Nano-30B-A3B`.

## Install

Python 3.11 or newer is required. Install [InferDoc 0.1.0 from PyPI](https://pypi.org/project/inferdoc/):

```bash
python3.11 -m pip install inferdoc
```

For source development, use `python3.11 -m pip install -e ".[dev]"` from the checkout. Live calls require your own `NEBIUS_API_KEY` and spend Nebius Token Factory credits. The offline replay does not need a key.

## 30-second offline check

The package supplies the SDK; the [repository](https://github.com/waqasm86/inferdoc) supplies sanitized example artifacts:

```bash
git clone https://github.com/waqasm86/inferdoc.git
cd inferdoc
python3.11 examples/05_replay_verification.py
```

This checks the artifact manifest and recomputes a captured verification result without contacting Nebius. It is one measured example, not a speedup guarantee.

## Python quickstart

These snippets make **live Token Factory requests** and spend credits:

```python
import inferdoc

response = inferdoc.chat(
    prompt="Define TTFT in one sentence.",
    max_tokens=32,
    temperature=0.0,
    chat_template_kwargs={"enable_thinking": False},
)
print(response.text)

run = inferdoc.benchmark(
    prompts=["Define TTFT.", "Define throughput."],
    concurrency=2,
    max_tokens=32,
    stream=False,
)
print(run.aggregate["latency_s"]["p95"])
print(run.aggregate["output_token_throughput_tps"])
```

The synchronous helpers use `asyncio.run`; use `NebiusClient.achat` or `AsyncBenchmarkRunner` inside an existing event loop. Non-streaming retains provider token usage when returned but has no TTFT. Streaming can observe first content, while the current streaming path does not retain usage. Unavailable metrics stay `None`.

## Closed loop

This command measures a baseline, calls Nemotron for diagnosis, checks the proposed change against a narrow concurrency policy, optionally reruns it, and verifies comparable evidence in Python. It makes live calls and spends credits:

```bash
inferdoc closed-loop --prompt "Define TTFT." --prompt "Define throughput." \
  --concurrency 1 --max-tokens 32
```

Python callers can use the `run_closed_loop` coroutine with `NebiusClient`, `WorkloadSpec`, and `ArtifactStore`; see the [closed-loop guide](docs/closed-loop.md). A missing or rejected proposal is valid. A candidate can legitimately yield `FAIL` or `INCONCLUSIVE`.

## Key capabilities and boundaries

- Bounded asynchronous benchmarks record per-request outcomes, aggregate latency percentiles, request throughput, and token throughput when usage is complete.
- `EvidenceBundle` separates backend support from values actually observed in a run.
- Nemotron uses read-only evidence tools and returns a typed `DiagnosisReport` with an optional `ExperimentSpec`.
- Deterministic admission rejects unsupported server controls; the default closed-loop demo changes only client concurrency 1–8.
- Python checks baseline/candidate workload comparability, metric objectives, and constraints before returning `PASS`, `FAIL`, or `INCONCLUSIVE`.
- `ArtifactStore` saves local JSON and canonical SHA-256 manifests. Evidence prompt fields are redacted by default, but other free text still needs review before sharing.

InferDoc targets hosted Token Factory. It does not expose serverless GPU utilization or KV-cache telemetry, run local CUDA/vLLM, guarantee an improvement, or turn model reasoning into measured facts. See [limitations](docs/limitations.md) and [security and privacy](docs/security-and-privacy.md).

## Documentation

The [documentation home](docs/README.md) links the full guide and [API reference](docs/api-reference.md). Start with [getting started](docs/getting-started.md), then [configuration](docs/configuration.md), [benchmarking](docs/benchmarking.md), [diagnosis](docs/diagnosis.md), [experiments](docs/experiments.md), [verification](docs/verification.md), and [CLI](docs/cli.md). [Examples](docs/examples.md), [notebooks](docs/notebooks.md), [artifacts](docs/artifacts.md), and [troubleshooting](docs/troubleshooting.md) cover practical use.

The five [Jupyter notebooks](notebooks/README.md) include the flagship live closed-loop walkthrough and a fully offline replay. Live notebook cells are opt-in and can spend credits.

## Testing and development

```bash
python3.11 -m pip install -e ".[dev]"
INFERDOC_RUN_LIVE_TESTS=0 python3.11 -m compileall -q src examples tests
INFERDOC_RUN_LIVE_TESTS=0 python3.11 -m pytest -q
```

Normal tests mock Token Factory; live integration tests remain skipped unless explicitly enabled. See [development](docs/development.md), [contributing](CONTRIBUTING.md), and the [release process](docs/release.md).

InferDoc is licensed under [Apache-2.0](LICENSE). Source, issues, and releases are at [GitHub](https://github.com/waqasm86/inferdoc).
