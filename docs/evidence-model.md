# Evidence model

`EvidenceBundle` is versioned and includes a run ID, backend/model identity,
workload and parameters, per-request measurements, capabilities, provenance,
and deterministic aggregate metrics. `RequestMeasurement` records UTC start,
first-response (when streaming yielded content), finish, success/error, and
token usage when the service returned it.

`EvidenceCapabilities` records separate support and run-level availability
flags. Non-streaming is the default: it can retain complete token usage but
does not observe TTFT. Streaming is explicit and may observe TTFT; the current
streaming client does not retain provider usage. GPU and KV-cache flags remain
unsupported and unavailable. `inferdoc bench` defaults to non-streaming;
`--stream` opts in to TTFT-oriented measurement.

Latency percentiles use the nearest-rank-free linear interpolation implemented
in `benchmark.metrics`. Request throughput uses successful requests divided by
wall-clock benchmark elapsed time. Output-token throughput uses returned
completion token counts. If usage or TTFT is unavailable, the corresponding
aggregate is `None`; no zero is substituted. Chunk boundaries are not called
TPOT or inter-token latency.

`ArtifactStore` writes `evidence.json`, an `audit.json` containing a SHA256
of canonical evidence, and `manifest.json` with canonical SHA256 hashes for
each saved artifact. Manifest updates replace one local JSON file atomically.
`verify_manifest` reports missing and changed files without repairing them.
JSON is intentionally human-readable and portable.

For fields, missing-value behavior, and local JSON storage, see [evidence](evidence.md), [benchmarking](benchmarking.md), and [artifacts](artifacts.md).
