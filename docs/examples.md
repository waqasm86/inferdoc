# Runnable examples

Run scripts from the repository root after installing InferDoc. The first four can make live Token Factory calls and spend credits; only example 04 has its own `INFERDOC_RUN_LIVE_TESTS=1` gate. **Do not run 01–03 merely to inspect them.**

| Script | Purpose | Requirements |
| --- | --- | --- |
| [`01_chat.py`](../examples/01_chat.py) | One Nemotron chat response | `NEBIUS_API_KEY`, credits |
| [`02_benchmark.py`](../examples/02_benchmark.py) | Two-prompt non-streaming benchmark and full evidence JSON | `NEBIUS_API_KEY`, credits |
| [`03_diagnose.py`](../examples/03_diagnose.py) | Diagnose a saved run by ID | Existing run, `NEBIUS_API_KEY`, credits for a new Nemotron call |
| [`04_closed_loop.py`](../examples/04_closed_loop.py) | Eight-prompt baseline and bounded full workflow | `NEBIUS_API_KEY`, `INFERDOC_RUN_LIVE_TESTS=1`, credits |
| [`05_replay_verification.py`](../examples/05_replay_verification.py) | Check sanitized manifest and recompute verification | Repository example artifacts only; offline |

Start safely with:

```bash
python3.11 examples/05_replay_verification.py
```

The [demo artifacts](../examples/demo_artifacts/README.md) are one captured outcome, not a benchmark promise. If you want to understand the steps before making live calls, read [getting started](getting-started.md), [benchmarking](benchmarking.md), [diagnosis](diagnosis.md), and [closed loop](closed-loop.md).
