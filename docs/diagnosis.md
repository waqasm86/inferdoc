# Diagnosis

`DoctorAgent` asks the configured Nemotron Doctor model to interpret an `EvidenceBundle`. It supplies three read-only tools: `get_run_summary`, `get_request_metrics`, and `get_backend_capabilities`. Tools return Python-derived evidence and a capability declaration; they do not run benchmarks, edit artifacts, or apply provider settings. Tool responses can include prompt text still held in the in-memory evidence bundle, so treat prompts and model responses as data sent to Token Factory.

`await DoctorAgent(client).adiagnose(bundle)` is the async API. `DoctorAgent(client).diagnose(bundle)` and top-level `inferdoc.diagnose(bundle, client=...)` are synchronous wrappers. The wrappers use `asyncio.run`, so use `adiagnose` inside an existing event loop. A new client is created and closed when none is supplied; a supplied client remains caller-owned. Diagnosis makes live model requests and spends credits even if the evidence bundle came from an offline file.

```python
import inferdoc
from inferdoc.storage import ArtifactStore

# Live Nemotron call; requires NEBIUS_API_KEY and spends credits.
bundle = ArtifactStore().load("YOUR_RUN_ID")
report = inferdoc.diagnose(bundle)
print(report.recommendation_summary)
```

`DiagnosisReport` has `measured_facts`, `derived_facts`, `hypotheses`, `missing_evidence`, `recommendation_summary`, optional `experiment`, optional `admission`, and `audit_log`. The agent allows up to three tool-bearing turns by default, then a synthesis turn if needed; schema-invalid JSON can receive up to two repair turns. Typed validation can still fail after that budget. If a proposed experiment fails deterministic admission, the report retains the rejected `AdmissionDecision` and clears the executable experiment.

Nemotron's facts and rationale are interpretations of tool output, not independent measurements. Python owns admission and the final [verification](verification.md). For a no-credit walkthrough, inspect the captured diagnosis in [notebook 02](../notebooks/02_nemotron_diagnosis.ipynb). See [experiments](experiments.md) and [security and privacy](security-and-privacy.md).
