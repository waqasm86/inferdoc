# Evidence

`inferdoc.evidence` exposes `EvidenceBundle`, `RequestMeasurement`, `EvidenceCapabilities`, and `canonical_sha256`. A bundle has schema version, run/backend/model identity, creation/completion timestamps, workload and generation parameters, request measurements, aggregate metrics, run capabilities, and provenance. It can be loaded from JSON with `EvidenceBundle.model_validate_json(...)` for offline analysis.

`RequestMeasurement` includes request ID, optional prompt text, prompt hash and length, UTC timing, success/error, optional input/output/total token counts, and response model. Its `e2e_latency_s` property is always derived from timestamps; `ttft_s` is `None` when no first-response timestamp exists. Failed requests contribute to total/failed counts but not successful-request latency and throughput numerators.

`EvidenceCapabilities` pairs `supports_*` flags with `*_available` flags. A metric can be supported by a backend but absent from a particular run. In the Token Factory client, GPU utilization and KV-cache metrics are marked unsupported and unavailable. Run-level flags are computed from the observed aggregate; they do not grant permission to change server controls.

`EvidenceBundle.with_aggregate(...)` calculates success rate, token totals, latency/TTFT summaries, and throughput. Complete token usage across successful requests is required for token totals and token throughput; partial data stays missing. The runner adds non-secret runtime provenance such as Python and InferDoc versions, endpoint host, and canonical workload/config hashes. Hashes support integrity and comparison; they do not encrypt data.

```python
from pathlib import Path
from inferdoc import EvidenceBundle

bundle = EvidenceBundle.model_validate_json(
    Path("examples/demo_artifacts/baseline.json").read_text(encoding="utf-8")
)
print(bundle.run_id, bundle.aggregate["successful_requests"])
print(bundle.capabilities.output_token_throughput_available)
```

Run this from the repository root for the example path. See [benchmarking](benchmarking.md) and [artifacts](artifacts.md).
