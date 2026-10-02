# Evidence model

`EvidenceBundle` is versioned and includes a run ID, backend/model identity,
workload and parameters, per-request measurements, capabilities, provenance,
and deterministic aggregate metrics. `RequestMeasurement` records UTC start,
first-response (when streaming yielded content), finish, success/error, and
token usage when the service returned it.

Latency percentiles use the nearest-rank-free linear interpolation implemented
in `benchmark.metrics`. Request throughput uses successful requests divided by
wall-clock benchmark elapsed time. Output-token throughput uses returned
completion token counts. If usage or TTFT is unavailable, the corresponding
aggregate is `None`; no zero is substituted. Chunk boundaries are not called
TPOT or inter-token latency.

`ArtifactStore` writes `evidence.json` and an `audit.json` containing a SHA256
of canonical evidence. JSON is intentionally human-readable and portable.
