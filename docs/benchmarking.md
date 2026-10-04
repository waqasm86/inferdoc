# Benchmarking

A `WorkloadSpec` has a nonempty ordered `prompts` list, `concurrency` (default 1), `max_tokens` (64), `temperature` (0.0), `stream` (False), and `enable_thinking` (False). Prompt strings cannot be blank. One request is scheduled per prompt; concurrency bounds how many run at once. `BenchmarkLimits` defaults to at most 32 requests and a 120-second wait for each `achat` call. The timeout does not cover the entire subsequent streaming iteration.

```python
from inferdoc import benchmark

# Live Token Factory call; requires NEBIUS_API_KEY and spends credits.
run = benchmark(
    prompts=["Define TTFT.", "Define throughput."],
    concurrency=2,
    max_tokens=32,
    stream=False,
)
print(run.aggregate["latency_s"]["p95"])
print(run.aggregate["output_token_throughput_tps"])
```

For an existing asynchronous client, use `await AsyncBenchmarkRunner(client).run(workload, model=...)` and close the client yourself. `benchmark` creates and closes its own client unless one is supplied. The synchronous convenience function uses `asyncio.run`; in a running event loop, use the async runner instead.

## Measurements

Each request records UTC start and finish timestamps, success or failure, an error string on failure, and provider token counts when returned. End-to-end latency is finish minus start. Streaming records the first nonempty content chunk as `first_response_at`; TTFT is available only when such a chunk is observed. Non-streaming requests do not observe TTFT. The current streaming parser yields text but does not retain usage, so token-throughput fields usually remain unavailable for streamed runs.

The aggregate reports request counts and success rate; mean/p50/p90/p95/p99 latency and TTFT; request throughput as successful requests divided by measured run elapsed time; and output/total token throughput when all successful requests have the required usage. Total token count can be derived from complete input and output counts if the provider omits combined total. Percentiles use linear interpolation. Missing data yields `None`, not zero. These are client-observed metrics, not server GPU or KV-cache telemetry.

`EvidenceCapabilities` distinguishes *backend support* from values *available in this run*. `TOKEN_FACTORY_CAPABILITIES` is the separate policy declaration for experiment admission. See [evidence](evidence.md), [experiments](experiments.md), and [limitations](limitations.md).
