# Hackathon alignment

InferDoc uses real runtime calls to Nebius Token Factory and NVIDIA Nemotron,
meeting the required technology for the Best Apps and Agents track.

**Technological implementation.** An asynchronous benchmark engine measures
requests; strict Pydantic schemas and SHA256 provenance make evidence portable;
Nemotron uses read-only function tools to interpret it; deterministic policy
admission blocks impossible controls; a second benchmark and Python verifier
establish the result.

**Design.** The coherent product experience is
`measure → diagnose → experiment → verify`. Users get one evidence bundle and
one auditable decision instead of disconnected charts or prose.

**Potential impact.** The target users are inference engineers and application
teams evaluating hosted LLM behavior who need to know whether a proposed
latency or throughput change actually helped under a fixed workload.

**Quality and creativity.** InferDoc is not a generic wrapper, dashboard,
provider router, or brute-force autotuner. Its distinctive rule is that an AI
recommendation must survive capability admission and empirical verification.
Python owns facts; Nemotron owns bounded reasoning.

The demo is intentionally small and credit-aware. Ordinary tests never call
Token Factory. Live examples require both an API key and
`INFERDOC_RUN_LIVE_TESTS=1`.

The optional closed-loop integration regression uses two short prompts and
accepts PASS, FAIL, INCONCLUSIVE, or a typed no-experiment outcome. Enabling it
spends Nebius credits. CI keeps `INFERDOC_RUN_LIVE_TESTS=0`.

**Judging walkthrough.** Notebook
[`03_closed_loop_experiment.ipynb`](../notebooks/03_closed_loop_experiment.ipynb)
is the flagship demonstration of Token Factory inference, Nemotron evidence
analysis, one admitted control change, and Python verification. Judges can
run [`04_offline_replay_and_audit.ipynb`](../notebooks/04_offline_replay_and_audit.ipynb)
without credentials or credits to inspect the measured example and hashes.
The product identity is an evidence-driven LLM inference doctor for Nebius
Token Factory. Serverless evidence does not claim GPU utilization, KV-cache
telemetry, or provider internals.
