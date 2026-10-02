# Reference design notes

The Token Factory cookbook establishes the OpenAI-compatible endpoint,
`NEBIUS_API_KEY`, streaming, and Nemotron model naming. vLLM and Ray informed
the meanings of TTFT, latency, token throughput, concurrency, and percentile
aggregation. InferenceX informed explicit, portable evidence artifacts;
Omniperf informed separating diagnosis from remediation; autotuner projects
informed pre-flight feasibility checks.

InferDoc does not copy their implementations and does not depend on vLLM, Ray,
Prometheus, DSPy, Pydantic AI, or a provider router. Native function calling
was chosen over a framework stack because the MVP needs a bounded read-only
tool loop and typed validation, not a second orchestration framework.
