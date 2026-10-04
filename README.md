# InferDoc

**Evidence-driven LLM Inference Doctor for Nebius Token Factory**

Built for the Nebius x NVIDIA Global AI Hackathon, Best Apps and Agents
track, with `nvidia/NVIDIA-Nemotron-3-Nano-30B-A3B`.

InferDoc is a small Python SDK for turning hosted inference observations into
controlled, experimentally verified decisions. Nebius Token Factory performs
hosted inference. InferDoc benchmarks that workload, stores reproducible evidence, asks NVIDIA Nemotron to
interpret that evidence and propose a bounded next experiment, admits or
rejects that proposal deterministically, then verifies the measured rerun.

The loop is:

```text
INFER → MEASURE → ANALYZE → DIAGNOSE → RECOMMEND → VALIDATE → RERUN → VERIFY
```

This makes InferDoc different from a playground, dashboard, API wrapper, or
autotuner: a model recommendation is only a hypothesis until Python checks it
against backend capabilities and a comparable benchmark.

## Install

For the public 0.1.0 release, after PyPI publication:

```bash
python3.11 -m pip install inferdoc
```

Until publication, install from this repository. For development:

```bash
python3.11 -m pip install -e ".[dev]"
```

Set `NEBIUS_API_KEY` for live calls. The default endpoint is
`https://api.tokenfactory.nebius.com/v1/`, and the default model is
`nvidia/NVIDIA-Nemotron-3-Nano-30B-A3B`.

## Minimal API

```python
import inferdoc

response = inferdoc.chat(
    model="nvidia/NVIDIA-Nemotron-3-Nano-30B-A3B",
    prompt="Hello!",
    max_tokens=64,
    temperature=0.0,
    chat_template_kwargs={"enable_thinking": False},
)
print(response.text)
```

For a bounded benchmark:

```python
run = inferdoc.benchmark(
    model="nvidia/NVIDIA-Nemotron-3-Nano-30B-A3B",
    prompts=["What is TTFT?", "Explain tensor parallelism briefly."],
    concurrency=2,
    max_tokens=32,
    stream=False,
    enable_thinking=False,
)
print(run.aggregate)
```

Non-streaming is the default because complete provider token usage supports
token-throughput evidence. Use `inferdoc bench --stream "prompt"` to opt in to
streaming TTFT measurement; this implementation does not retain streaming
token usage, so token-throughput metrics can be unavailable. Run-level
`EvidenceCapabilities` separates backend support from values observed in a
particular run. GPU utilization and KV-cache telemetry are unsupported.

Use `inferdoc.diagnose(run)` to obtain a typed `DiagnosisReport`, then admit
its `ExperimentSpec` with `inferdoc.validate_experiment`. The closed-loop
example shows the complete lifecycle.

## Closed-loop CLI

```bash
inferdoc closed-loop \
  --prompt "Explain TTFT briefly." \
  --prompt "Explain throughput briefly." \
  --concurrency 1 --max-tokens 64
```

Pass `--prompts-file prompts.txt` for one prompt per line. The command writes
artifacts to `.inferdoc/runs` by default; `--artifact-dir` changes that path.
Workload requests default to non-streaming and thinking disabled. The Doctor
uses Nemotron reasoning separately. The JSON summary includes run IDs,
admission, verification status, metric results, and artifact directory.
Exit code 0 means the workflow completed, including a measured FAIL or
INCONCLUSIVE or no executable recommendation. Exit code 2 means deterministic
admission rejected a proposed experiment. Exit code 1 means a runtime failure.
The reusable `inferdoc.run_closed_loop` coroutine provides the same workflow
to Python callers.

## Offline replay and artifact integrity

`python3.11 examples/05_replay_verification.py` replays sanitized evidence
from one measured closed-loop run. It needs no API key, network, or Token
Factory credits. `ArtifactStore` records canonical SHA-256 hashes for saved
evidence, diagnosis, experiment, and verification JSON in each run's
`manifest.json`; `verify_manifest` detects missing or changed files. The
example is one captured outcome, not a performance guarantee.

## Judge testing instructions

Quick test without Nebius credits, using the public package after publication:

```bash
python3.11 -m pip install inferdoc
git clone https://github.com/waqasm86/inferdoc.git
cd inferdoc
python3.11 examples/05_replay_verification.py
```

Before PyPI publication, clone the repository first and run
`python3.11 -m pip install -e .` inside it. The replay checks sanitized measured
evidence, artifact-manifest integrity, and deterministic verification.

For an optional live Token Factory check, set your own key in your shell and
explicitly enable live tests:

```bash
python3.11 -m pip install pytest
export NEBIUS_API_KEY=... # replace the placeholder in your own shell
export INFERDOC_RUN_LIVE_TESTS=1
python3.11 -m pytest -q tests/integration/test_live_smoke.py -s
python3.11 -m pytest -q tests/integration/test_live_closed_loop.py -s
```

Live tests spend Nebius Token Factory credits. The offline replay does not.

## Jupyter notebooks

Install the optional notebook tools with
`python3.11 -m pip install -e ".[notebooks]"`, then launch Jupyter from the
repository root. The notebooks import the real InferDoc package:

| Notebook | Stage |
| --- | --- |
| `00_token_factory_quickstart.ipynb` | Token Factory quickstart |
| `01_benchmark_evidence.ipynb` | Evidence benchmarking |
| `02_nemotron_diagnosis.ipynb` | Nemotron diagnosis and admission |
| `03_closed_loop_experiment.ipynb` | Complete closed loop, flagship demo |
| `04_offline_replay_and_audit.ipynb` | Offline replay and manifest audit |

Notebooks 00–03 may spend Token Factory credits only when their live gate is
explicitly enabled; notebook 04 is completely offline. See
[notebooks/README.md](notebooks/README.md) for setup and per-notebook behavior.

## What is deterministic?

Python owns timestamps, request outcomes, token usage, latency percentiles,
throughput, comparisons, capability checks, thresholds, and PASS/FAIL/
INCONCLUSIVE. Nemotron owns interpretation, hypotheses, missing-evidence
questions, and experiment rationale. It cannot execute shell commands or edit
evidence, and its proposed controls are rejected when Token Factory does not
expose them.

`PASS` means the candidate met every requested objective and constraint;
`FAIL` means comparable evidence disproved the objective or violated a
constraint; `INCONCLUSIVE` means required evidence or comparability was
missing. Missing values remain `None`, never zero.

## Closed-loop demo

`examples/04_closed_loop.py` makes a deliberately small number of live calls
only when `INFERDOC_RUN_LIVE_TESTS=1` and `NEBIUS_API_KEY` are set:

```bash
INFERDOC_RUN_LIVE_TESTS=1 python3.11 examples/04_closed_loop.py
```

It performs a baseline benchmark, Nemotron tool-driven diagnosis, admission,
candidate benchmark, and deterministic verification. A failed or inconclusive
result is a valid scientific outcome; the example never fabricates success.

`tests/integration/test_live_closed_loop.py` is an optional live regression.
It spends Nebius credits only when `INFERDOC_RUN_LIVE_TESTS=1` and
`NEBIUS_API_KEY` are both set. Normal CI fixes the gate to `0` and skips this
test. It checks workflow structure, not a guaranteed speedup or PASS result.

## Why the product exists

Prometheus/Grafana can show metrics but do not formulate and verify a bounded
next experiment. LiteLLM normalizes providers but is not an inference study.
Autotuners search parameter spaces, while InferDoc asks one evidence-grounded
question and checks the answer cheaply. Nemotron is useful here as a bounded
reasoning layer over structured facts, while Python remains the authority for
measurement.

## Layout

```text
src/inferdoc/{nebius,benchmark,evidence,doctor,experiments,verification,storage}
examples/                  small runnable workflows
docs/                      architecture, schemas, hackathon mapping
tests/                     offline unit tests; live tests are opt-in
```

See [docs/architecture.md](docs/architecture.md), [docs/evidence-model.md](docs/evidence-model.md),
[docs/experiment-model.md](docs/experiment-model.md), and
[docs/hackathon.md](docs/hackathon.md). InferDoc uses `httpx` directly so the
core install stays small; an optional `openai` extra is available for projects
that already use the official OpenAI client.

## Security and scope

Keys come from the environment and are never written to evidence. Prompt text is redacted from persisted evidence by default. InferDoc keeps prompt hashes,
lengths, token counts, timings, and aggregate metrics. A caller must explicitly opt in with
`ArtifactStore(store_prompts=True)` to persist raw prompt text. InferDoc has no GPU, CUDA, vLLM, Ray, Kaggle, or multi-cloud dependency.
Dedicated-endpoint observability is an optional future adapter; ordinary
serverless Token Factory calls do not imply GPU utilization or KV-cache telemetry.

## License

Apache-2.0. Copyright 2026 InferDoc contributors. Design influences are documented without vendoring reference
implementations.

## Hackathon evidence contract

```text
Nebius Token Factory performs inference
        ↓
Python measures and aggregates evidence
        ↓
NVIDIA Nemotron interprets read-only evidence and proposes one bounded experiment
        ↓
Python validates backend capabilities and policy
        ↓
InferDoc reruns the controlled workload
        ↓
Python returns PASS / FAIL / INCONCLUSIVE
```

InferDoc does not treat Nemotron output as measurement truth. Numerical metrics,
capability admission, constraints, comparisons, and verification outcomes are
computed deterministically from observed requests.

For the hackathon demo, `examples/04_closed_loop.py` deliberately limits the
automatic experiment to one changed variable: client concurrency. Model, prompt
set, temperature, maximum output tokens, and streaming mode remain controlled.

## Build a release

```bash
python3.11 -m pip install -e ".[dev]"
python3.11 -m compileall -q src examples tests
INFERDOC_RUN_LIVE_TESTS=0 python3.11 -m pytest -q
python3.11 -m build --no-isolation
python3.11 -m twine check dist/*
```

The repository includes `.github/workflows/release.yml` for PyPI Trusted
Publishing. Publishing is triggered by a GitHub Release after the matching
Trusted Publisher is configured on PyPI.
