# Python API reference

This hand-maintained reference describes the public exports in InferDoc 0.1.0 source. Imports and signatures below were checked against the package; `**kwargs` remains open-ended where the implementation uses it. Live-call examples require `NEBIUS_API_KEY` and spend Token Factory credits. Follow the linked guides for runnable examples.

## Top-level `inferdoc` API

| Object / import | Important signature or fields | Return and notes |
| --- | --- | --- |
| `InferDocSettings` | Dataclass: `api_key=None`, `base_url`, `default_model`, `doctor_model`, `timeout_s=120.0`, `max_retries=2`, `artifact_dir=".inferdoc/runs"` | `from_env(**overrides)` loads environment; `require_api_key()` raises `ConfigurationError` if absent; `normalized_base_url()` returns slash-terminated URL. [Configuration](configuration.md). |
| `NebiusClient` | `NebiusClient(settings=None, *, api_key=None, base_url=None, timeout_s=None, transport=None)` | Async HTTP client; close with `await aclose()` or `async with`. `achat(*, model=None, prompt=None, messages=None, stream=False, **parameters)` returns `ChatResponse` or async text iterator; `astream(**kwargs)` yields text; `chat(**kwargs)` is synchronous non-streaming and closes the client. Provider/connection failures raise `BackendError`. [Getting started](getting-started.md). |
| `chat` | `chat(**kwargs)` | One-shot synchronous non-streaming `ChatResponse`; accepts `prompt` or `messages`, optional `model`, and provider parameters such as `max_tokens`. It creates/closes a client. Use `NebiusClient.achat` in an event loop. |
| `BenchmarkLimits` | `BenchmarkLimits(max_requests=32, timeout_s=120.0)` | Pydantic model for request-count and per-call wait limits. |
| `AsyncBenchmarkRunner` | `AsyncBenchmarkRunner(client, *, limits=None)`; `await run(workload, *, model=None)` | Returns `EvidenceBundle`; supplied client is caller-owned. Requires a `ChatLike` object with async `achat`. |
| `benchmark` | `benchmark(*, prompts, model=None, concurrency=1, max_tokens=64, temperature=0.0, stream=False, enable_thinking=False, client=None, limits=None)` | Synchronous `EvidenceBundle`; creates/closes a client unless supplied. Uses `asyncio.run`, so use the async runner inside an event loop. [Benchmarking](benchmarking.md). |
| `EvidenceBundle` | Pydantic model with `run_id`, `backend`, `model`, timestamps, `requests`, `workload`, `parameters`, `aggregate`, `capabilities`, `provenance`; `with_aggregate(**kwargs)` | Captured measurement and deterministic aggregate. Missing measurements stay `None`. [Evidence](evidence.md). |
| `DoctorAgent` | `DoctorAgent(client=None, *, capabilities=None, max_tool_rounds=3, max_schema_repairs=2)`; `await adiagnose(bundle)` / `diagnose(bundle)` | Returns `DiagnosisReport`; supplied client stays caller-owned. Diagnosis makes model calls; schema errors can survive bounded repair. [Diagnosis](diagnosis.md). |
| `diagnose` | `diagnose(bundle, *, client=None)` | Synchronous `DiagnosisReport` from a live Doctor call. |
| `ExperimentSpec` | Required: `id`, `hypothesis`, `model`, `baseline_run_id`, nonempty `changed_variables` and `controlled_variables`, `objective`, nonempty `verification_metrics`, `rationale`; optional `backend`, `constraints` | Typed proposed change; construction/JSON parsing can raise Pydantic validation errors. [Experiments](experiments.md). |
| `BackendCapabilities` | `backend`, `controllable_fields`, `observable_fields`, `domains` | Backend admission declaration, separate from run-observed `EvidenceCapabilities`. |
| `AdmissionDecision` | `approved`, `reasons`, `experiment_id` | Deterministic admission result. |
| `validate_experiment` | `validate_experiment(experiment, capabilities, *, baseline=None, max_requests=64, max_changed_variables=None)` | Returns `AdmissionDecision`; missing baseline rejects. It does not run a benchmark. [Experiments](experiments.md). |
| `VerificationStatus` | `PASS`, `FAIL`, `INCONCLUSIVE` | String enum for deterministic result. |
| `VerificationReport` | `status`, baseline/candidate/experiment IDs, `metric_results`, `constraint_results`, `reasons` | Structured verifier output. |
| `verify` | `verify(*, baseline, candidate, experiment)` | Returns `VerificationReport` without network calls. [Verification](verification.md). |
| `ClosedLoopResult` | `baseline`, `diagnosis`, optional `admission`, `candidate`, `verification` | Workflow output; optional fields can be `None` when there is no executable proposal. |
| `run_closed_loop` | `async run_closed_loop(*, client, workload, model=None, capabilities=DEMO_TOKEN_FACTORY_CAPABILITIES, artifact_store=None)` | Returns `ClosedLoopResult`; owns no supplied client. Default policy changes only concurrency 1–8. Raises if baseline has no successes. [Closed loop](closed-loop.md). |
| `ObservabilitySnapshot` | `source`, `window_start`, `window_end`, optional `metrics` and `labels` | Typed holder for external metrics; it does not fetch serverless GPU metrics. |
| `UnsupportedObservabilityAdapter` | `query(*, endpoint, window)` | Raises `NotImplementedError` for unavailable dedicated-endpoint telemetry. [Limitations](limitations.md). |

## Configuration and Nebius models

`inferdoc.config.InferDocSettings` is the same top-level settings class. `inferdoc.nebius.ChatResponse` has `text`, optional `reasoning_content`, `finish_reason`, `model`, `response_id`, `usage`, and `raw`. `inferdoc.nebius.models.TokenUsage` has optional prompt, completion, and total counts. `NebiusClient.raw` is an `httpx.AsyncClient`; callers using it directly own any lower-level behavior. `inferdoc.exceptions` defines `InferDocError`, `ConfigurationError`, `BackendError`, `AdmissionError`, and `EvidenceError`; not every operation uses every exception subclass.

## Benchmark and evidence modules

- `inferdoc.benchmark.WorkloadSpec(prompts, concurrency=1, max_tokens=64, temperature=0.0, stream=False, enable_thinking=False)` validates a nonempty prompt list, positive concurrency/max tokens, and nonnegative temperature. `AsyncBenchmarkRunner` and `benchmark` are also re-exported here.
- `inferdoc.evidence.RequestMeasurement` stores request ID, optional prompt/hash/length, timestamps, success/error, optional token counts, and model. Read-only properties `e2e_latency_s` and `ttft_s` derive timings.
- `inferdoc.evidence.EvidenceCapabilities` has `supports_*` and run-level `*_available` flags. `canonical_sha256(value)` returns the hash of canonical JSON for the value.
- `EvidenceBundle.with_aggregate(...)` is used by the runner to calculate counts, percentiles, throughput, and availability. Constructing a plain `EvidenceBundle` does not recalculate its aggregate.

## Doctor module

`inferdoc.doctor.DiagnosisReport` stores lists of measured and derived facts, hypotheses, missing evidence, recommendation text, optional `ExperimentSpec` and `AdmissionDecision`, and tool audit entries. `DoctorAgent` and `diagnose` are re-exported by `inferdoc.doctor`. Read-only tool definitions are implementation support, not the primary SDK interface.

## Experiment module

- `inferdoc.experiments.MetricRule(metric, direction, minimum_relative_change=0.0, maximum_relative_regression=None)` describes a relative objective. `MetricDirection` lives at `inferdoc.experiments.models` and is `maximize` or `minimize`. The current verifier does **not** use `maximum_relative_regression`.
- `inferdoc.experiments.Constraint(metric, maximum=None, minimum=None)` requires exactly one bound; it checks a candidate aggregate metric.
- `inferdoc.experiments.TOKEN_FACTORY_CAPABILITIES` declares general client controls and observable roots. `DEMO_TOKEN_FACTORY_CAPABILITIES` is available from `inferdoc.experiments.capabilities` for the narrower closed-loop demo.
- `inferdoc.experiments.policy.validate_experiment` is the same top-level function. `inferdoc.experiments.runner.run_experiment` executes an admitted candidate asynchronously; it can still fail if the backend rejects a request.

## Verification, storage, and workflows

`inferdoc.verification.compare_workloads(baseline, candidate, experiment)` returns `ComparabilityReport(mismatches, missing)` with a derived `comparable` property. `VerificationReport.metric_results` contains `MetricEvaluation` items; `constraint_results` contains `ConstraintEvaluation` items, each recording an optional pass value and reason.

`inferdoc.storage.ArtifactStore(root=".inferdoc/runs", *, store_prompts=False)` has `save(bundle)`, `load(run_id)`, `save_diagnosis(report, run_id)`, `save_experiment(experiment, run_id)`, `save_verification(report, run_id)`, `link_closed_loop(...)`, `verify_manifest(run_id)`, and `list_runs()`. `verify_manifest` returns `ManifestVerification(valid, missing, changed)`. See [artifacts](artifacts.md) for file layout and privacy limits.

`inferdoc.workflows.run_closed_loop` and `ClosedLoopResult` are the same top-level workflow exports. The supplied client is closed by the caller, as in the [closed-loop example](closed-loop.md).
