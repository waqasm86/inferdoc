# Experiment model

An `ExperimentSpec` is a falsifiable change proposal. It names a baseline run,
model and backend, lists changed variables, states controlled variables,
defines a measurable objective, and carries metric rules plus hard constraints.

`BackendCapabilities` is the admission authority. For Token Factory the
client can control model, temperature, max tokens, streaming, prompt set, and
client concurrency. It cannot control tensor parallelism, GPU memory,
batching, or server scheduler settings. Such proposals are rejected before
they spend inference budget.

Verification compares only compatible identities, evaluates every metric rule
and constraint, and returns `PASS`, `FAIL`, or `INCONCLUSIVE`. Nemotron can
explain a result afterward but cannot decide it.
