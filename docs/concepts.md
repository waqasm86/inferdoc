# Concepts

InferDoc helps answer one constrained question: did a proposed change help for a measured workload? The lifecycle is:

```text
INFER → MEASURE → ANALYZE → DIAGNOSE → RECOMMEND → VALIDATE → RERUN → VERIFY
```

Nebius Token Factory serves inference. Python records request timing, outcomes, provider token usage when available, aggregates, provenance, admission decisions, workload comparisons, and final verdicts. NVIDIA Nemotron interprets the evidence through read-only tools and may propose one typed `ExperimentSpec`. Its recommendation is a hypothesis, not a measured result.

## Baseline and candidate

A baseline `EvidenceBundle` contains the initial prompt workload and its measurements. An admitted experiment changes declared controls. The candidate rerun is another `EvidenceBundle`. Verification checks backend/model identity, ordered prompt hashes, changed values, held controls, and other workload drift before evaluating metrics.

## Admission and verdict

`validate_experiment` checks proposed controls and observable metric roots against a declared backend capability set. The closed-loop workflow uses a narrower demo policy: at most one changed field and client concurrency 1–8. Admission says an experiment is permitted; it does not say the experiment will improve performance or that a metric appeared in a particular run.

Python returns `PASS` when comparable evidence meets every objective and constraint; `FAIL` when a measured threshold or workload identity fails; `INCONCLUSIVE` when necessary evidence or comparability data is missing. Missing values remain unavailable rather than becoming zero. A zero baseline also makes relative-change verification inconclusive.

Continue with [benchmarking](benchmarking.md), [experiments](experiments.md), [verification](verification.md), and [closed loop](closed-loop.md).
