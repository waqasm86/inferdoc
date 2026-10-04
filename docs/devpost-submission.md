# Devpost submission draft

- **Project name:** InferDoc
- **Track:** Best Apps and Agents
- **Tagline:** Evidence-driven LLM inference doctor for Nebius Token Factory.
- **GitHub:** https://github.com/waqasm86/inferdoc
- **PyPI:** [pending verified publication of `inferdoc==0.1.0`]
- **Working demo/test build:** https://github.com/waqasm86/inferdoc (Python SDK/CLI and offline replay; add the GitHub Release URL after release)
- **Public YouTube demo:** [MANUAL USER TASK — add public <=3 minute YouTube URL before Devpost submission]

## Problem

Hosted LLM users can change concurrency and generation settings, but a faster
response in one ad hoc trial does not establish a reliable inference improvement.
They need measured evidence, a bounded next experiment, and a deterministic
check that the candidate workload was comparable.

## Audience

Inference engineers and application teams evaluating latency and throughput
on Nebius Token Factory.

## Solution

InferDoc benchmarks a controlled prompt workload, stores per-request and
aggregate evidence, asks NVIDIA Nemotron to interpret it through read-only
tools, and admits at most one executable change. It reruns the candidate and
verifies objectives and constraints in Python. The CLI, reusable Python SDK,
five notebooks, offline replay, and hashed artifact manifests make the loop
inspectable without a dashboard.

## Architecture

`INFER → MEASURE → ANALYZE → DIAGNOSE → RECOMMEND → VALIDATE → RERUN → VERIFY`

Nebius Token Factory hosts and serves inference. Python records timings,
provider token usage when available, success/failure, throughput, and
provenance. Nemotron-3 Nano reads structured evidence and proposes a
hypothesis with an `ExperimentSpec`. Python checks backend control admission,
workload comparability, objective thresholds, and constraints, then returns
PASS, FAIL, or INCONCLUSIVE.

## How Nebius Token Factory is used

InferDoc sends real inference requests to the Token Factory OpenAI-compatible
endpoint. The default workload model is
`nvidia/NVIDIA-Nemotron-3-Nano-30B-A3B`. Non-streaming requests retain
provider token usage for throughput evidence. Streaming is optional for TTFT.

## How NVIDIA Nemotron is used

The same NVIDIA Nemotron-3 Nano model is the bounded Doctor reasoning engine.
It uses read-only functions for run summary, request metrics, and backend
capabilities. This is useful rather than cosmetic: it turns multiple measured
facts into a specific, falsifiable experiment, identifies unavailable
evidence, and explains its rationale. Its report is schema validated and may
be repaired within a bounded model-call budget.

## Deterministic safety and measurement boundary

Nemotron cannot edit measurements, claim unobserved GPU or KV-cache metrics,
admit unsupported controls, or declare the final outcome. Python owns
measurement, aggregation, capability availability, admission, rerun workload
comparison, thresholds, and PASS/FAIL/INCONCLUSIVE. Prompt text is redacted
from saved evidence by default; canonical SHA-256 manifests detect changed
artifacts.

## One measured demonstration result

A captured Token Factory run on 2026-10-02 used eight short prompts at client
concurrency 1, then changed only concurrency to 2. Measured output-token
throughput rose from **29.44 to 151.66 tokens/s**; p95 latency was **5.15 s**
for the baseline and **0.93 s** for the candidate. Deterministic verification
returned **PASS** for that experiment's declared throughput objective.
This is one observed run, **not a universal performance guarantee**. Its
sanitized artifacts and hashes are in `examples/demo_artifacts/`.

## Limitations

Serverless Token Factory does not expose GPU utilization, KV-cache metrics,
or internal scheduler telemetry through this client. Non-streaming evidence
has no TTFT; current streaming evidence may lack provider token usage. Model
recommendations can be rejected, and a comparable rerun can legitimately be
FAIL or INCONCLUSIVE. Performance varies with service conditions.

## Setup and testing

InferDoc is a Python SDK/CLI test build, not a hosted graphical application.
Use Python 3.11. After PyPI publication, install with
`python3.11 -m pip install inferdoc`; until then, clone the repository and use
`python3.11 -m pip install -e .`. Run the no-credit replay with
`python3.11 examples/05_replay_verification.py` or notebook 04. It checks
sanitized measured evidence, artifact integrity, and deterministic verification.
Run offline tests with `INFERDOC_RUN_LIVE_TESTS=0 python3.11 -m pytest -q`.
For live checks, install pytest with `python3.11 -m pip install pytest`, set
your own `NEBIUS_API_KEY`, set
`INFERDOC_RUN_LIVE_TESTS=1`, then run
`python3.11 -m pytest -q tests/integration/test_live_smoke.py -s` and
`python3.11 -m pytest -q tests/integration/test_live_closed_loop.py -s`.
Live tests spend Nebius Token Factory credits. Notebook 03 is the flagship
end-to-end walkthrough.

## Nebius and NVIDIA feedback

The OpenAI-compatible Token Factory API kept integration small. Nemotron Nano
tool calling was effective for bounded evidence analysis. Structured output
still requires schema validation and bounded repair. Explicit documentation
of reasoning controls, streaming usage availability, and telemetry discovery
would help inference engineering tools. See `docs/feedback-notes.md` for
implementation details.

## Significant update statement

InferDoc was created as a standalone project during the Nebius x NVIDIA Global
AI Hackathon submission period. It does not depend on my earlier kaggle-vllm or
kaggle-vllm-nebius projects.
