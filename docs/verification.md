# Deterministic verification

`verify(*, baseline, candidate, experiment)` returns a `VerificationReport` with `status`, both run IDs, experiment ID, per-metric results, constraint results, and reasons. It makes no provider request. `VerificationStatus` has `PASS`, `FAIL`, and `INCONCLUSIVE`.

Before judging metrics, `compare_workloads` checks backend/model identity, experiment baseline ID, ordered prompt hashes, actual request prompts against declared workload, declared changed and controlled values, and drift in other `WorkloadSpec` fields. A mismatch is `FAIL`; missing comparison data is `INCONCLUSIVE` unless there is already a mismatch.

A metric rule reads an aggregate field or dotted subfield such as `latency_s.p95`. It compares candidate and baseline relative to the absolute baseline, in the rule's direction, against `minimum_relative_change`. A missing metric or zero baseline leaves the relative result undefined and yields `INCONCLUSIVE` unless another comparison mismatch already makes the report `FAIL`. A measured threshold miss or violated candidate constraint is `FAIL`; all comparable, observed, satisfied rules and constraints yield `PASS`. `maximum_relative_regression` is not currently evaluated; use `Constraint` for an enforced bound.

```python
from pathlib import Path
from inferdoc import EvidenceBundle, ExperimentSpec, verify

root = Path("examples/demo_artifacts")
baseline = EvidenceBundle.model_validate_json((root / "baseline.json").read_text())
candidate = EvidenceBundle.model_validate_json((root / "candidate.json").read_text())
experiment = ExperimentSpec.model_validate_json((root / "experiment.json").read_text())
report = verify(baseline=baseline, candidate=candidate, experiment=experiment)
print(report.status, report.reasons)
```

Run this from the repository root. The [offline replay](../examples/05_replay_verification.py) also checks the captured artifact manifest. A captured `PASS` is one measured result, not a guaranteed speedup. See [concepts](concepts.md) and [artifacts](artifacts.md).
