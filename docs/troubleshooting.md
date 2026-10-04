# Troubleshooting

## Authentication and provider calls

- **Missing `NEBIUS_API_KEY`:** `InferDocSettings.require_api_key()` raises `ConfigurationError` for live calls. Set the key in your local environment or ignored `.env`. Offline replay and `inferdoc runs` do not need it.
- **HTTP errors or connection failures:** `NebiusClient` raises `BackendError`. Check endpoint/model configuration and provider response status. Non-streaming 5xx and transport errors can be retried up to `max_retries`; other HTTP errors are returned as errors. Streaming uses a separate path and is not retried by this loop.
- **Timeouts:** Set `INFERDOC_TIMEOUT_S` for the HTTP client. `BenchmarkLimits.timeout_s` bounds the awaited `achat` call; streaming chunk iteration is not covered by that runner wait. A request failure remains recorded as failed evidence.

## Missing metrics and experiment outcomes

- **No TTFT:** Non-streaming has no first-content timestamp. Use streaming if TTFT matters, and expect `None` if no content chunk arrives.
- **No token throughput:** The provider may omit usage, or current streaming mode may not retain it. Missing counts are not zero. Use non-streaming when provider token usage is needed.
- **Rejected `ExperimentSpec`:** Inspect `AdmissionDecision.reasons`. Token Factory controls are limited; server knobs such as tensor parallelism are unsupported through this policy. The closed-loop demo has a narrower concurrency-only policy.
- **`INCONCLUSIVE`:** Inspect `VerificationReport.reasons` and per-metric `reason`. Required evidence, comparable workload information, or a nonzero baseline for a relative comparison may be missing. Rerun with a workload that observes the required metric; do not relabel missing data as FAIL.
- **Manifest invalid:** `verify_manifest` lists missing and changed artifact names. Restore from a trusted copy or rerun the workflow; it does not repair files.

## Installation and discovery

- **`ModuleNotFoundError`:** Check `python3.11 -m pip show inferdoc` and run with the same Python 3.11 installation. In a source checkout, `python3.11 -m pip install -e .` installs the package locally.
- **PyPI website search omits InferDoc:** The [direct project page](https://pypi.org/project/inferdoc/) and `python3.11 -m pip install inferdoc` are separate from website search. A missing search listing does not by itself establish a package upload failure.

See [configuration](configuration.md), [benchmarking](benchmarking.md), [verification](verification.md), and [security](security-and-privacy.md).
