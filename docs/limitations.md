# Current limitations

- InferDoc targets hosted Nebius Token Factory. It has no generic multi-cloud backend layer and does not run local CUDA, vLLM, or server scheduling code.
- The current serverless integration records client-side request evidence. It does not measure GPU utilization, KV-cache occupancy, or direct provider internals. `UnsupportedObservabilityAdapter` raises rather than inventing those values.
- Non-streaming requests can retain provider usage but do not observe TTFT. Streaming can observe first content but currently does not retain token usage, so token throughput may be unavailable.
- A benchmark has one request per prompt and a default 32-request limit. Results describe that workload and service conditions; no speedup is guaranteed.
- Nemotron diagnosis is a hypothesis. It can produce no experiment, an inadmissible experiment, or an invalid report after bounded repair. Python admission and verification remain authoritative.
- `MetricRule.maximum_relative_regression` is present in the schema but not evaluated by the current verifier. Use an explicit `Constraint` for an enforceable bound.
- Verification requires comparable workload evidence and observable metrics. Missing data can produce `INCONCLUSIVE`; a zero baseline makes relative comparison undefined.
- Artifacts are local JSON with hashes, not encrypted or externally signed. Default evidence prompt redaction does not sanitize every free-text field.

See [architecture](architecture.md), [benchmarking](benchmarking.md), [verification](verification.md), and [security and privacy](security-and-privacy.md).
