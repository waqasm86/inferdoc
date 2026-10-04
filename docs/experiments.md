# Experiments and admission

`ExperimentSpec` is a typed, falsifiable proposal: `id`, `hypothesis`, `backend`, `model`, `baseline_run_id`, nonempty `changed_variables` and `controlled_variables`, `objective`, at least one `verification_metrics` rule, optional `constraints`, and `rationale`. `MetricRule` names an aggregate metric path such as `latency_s.p95`, a `MetricDirection` (`maximize` or `minimize`), and a minimum relative change. `Constraint` supplies exactly one minimum or maximum bound. The schema also contains `maximum_relative_regression`, but the current verifier does not evaluate that field; use an explicit `Constraint` for an enforceable hard bound.

`BackendCapabilities` declares a backend name, controllable fields, observable metric roots, and numeric domains. The Token Factory policy declares controls `temperature`, `max_tokens`, `stream`, `concurrency`, and `prompts`; observables `latency_s`, `ttft_s`, `request_throughput_rps`, `output_token_throughput_tps`, `total_token_throughput_tps`, and `token_usage`. Numeric domains are concurrency 1–64, max tokens 1–4096, and temperature 0–2. These are InferDoc admission bounds, not a promise that a particular model or run supports every value or returns every observable.

`validate_experiment(experiment, capabilities, baseline=..., max_requests=64, max_changed_variables=None)` returns an `AdmissionDecision` with `approved`, `reasons`, and `experiment_id`. It rejects backend mismatch, unsupported controls or metric roots, out-of-domain/invalid control values, missing baseline evidence, too many prompts, overlapping changed/controlled fields, and an optional changed-field limit. The closed-loop workflow passes a one-field limit and a narrower demo capability policy: only concurrency 1–8 can change. Admission does not verify that a metric was observed; [verification](verification.md) handles missing run data.

```python
from pathlib import Path
from inferdoc import ExperimentSpec, validate_experiment
from inferdoc.evidence import EvidenceBundle
from inferdoc.experiments import TOKEN_FACTORY_CAPABILITIES

root = Path("examples/demo_artifacts")
baseline = EvidenceBundle.model_validate_json((root / "baseline.json").read_text())
proposal = ExperimentSpec.model_validate_json((root / "experiment.json").read_text())
decision = validate_experiment(proposal, TOKEN_FACTORY_CAPABILITIES, baseline=baseline)
print(decision.approved, decision.reasons)
```

From the repository root, this captured proposal is admitted. Replacing its `changed_variables` with `{"tensor_parallel_size": 2}` yields a rejection because Token Factory does not expose that server control through InferDoc. An admission decision is a permission check, not a prediction of improvement. See [closed loop](closed-loop.md) for execution and [capability versus availability](benchmarking.md#measurements).
