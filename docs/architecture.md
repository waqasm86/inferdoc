# Architecture

InferDoc has six deliberately small boundaries:

1. `nebius` sends OpenAI-compatible requests to Token Factory and normalizes
   errors and usage.
2. `benchmark` schedules bounded asynchronous requests and records request
   timing without inferring token timing that the API did not provide.
3. `evidence` and `storage` validate, hash, and persist transparent JSON.
4. `doctor` exposes read-only evidence tools to Nemotron and validates its
   typed report.
5. `experiments` describes changes, controls, objectives, and constraints;
   policy admission rejects controls the backend cannot execute.
6. `verification` compares baseline and candidate facts using Python only.

```text
Token Factory → BenchmarkRunner → EvidenceBundle → read-only tools → Nemotron
                                      ↑                              ↓
                         Verification ← Candidate ← Policy ← ExperimentSpec
```

The core uses `httpx` instead of wrapping every OpenAI feature. This keeps the
dependency surface small and makes streaming timing and error handling explicit.
The raw HTTP client remains available as `NebiusClient.raw`.
