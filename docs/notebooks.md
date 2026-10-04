# Jupyter notebooks

The five notebooks use the installed InferDoc SDK and have cleared execution outputs. Launch them from the repository root so relative paths to sanitized artifacts work. Optional notebook tools are installed with `python3.11 -m pip install -e ".[notebooks]"`; see the [notebook README](../notebooks/README.md).

| Notebook | Main purpose | Default behavior | Live opt-in |
| --- | --- | --- | --- |
| [`00_token_factory_quickstart`](../notebooks/00_token_factory_quickstart.ipynb) | One short hosted chat | Skips the call | `INFERDOC_RUN_LIVE_TESTS=1` and key |
| [`01_benchmark_evidence`](../notebooks/01_benchmark_evidence.ipynb) | Run or inspect measured evidence and provenance | Loads captured baseline | Same gate for a new benchmark; streaming comparison needs a separate `RUN_STREAMING_DEMO=True` switch |
| [`02_nemotron_diagnosis`](../notebooks/02_nemotron_diagnosis.ipynb) | Read-only tools, captured diagnosis, policy admission | Uses captured evidence and diagnosis | Same gate plus separate `RUN_LIVE_DIAGNOSIS=True` switch |
| [`03_closed_loop_experiment`](../notebooks/03_closed_loop_experiment.ipynb) | Flagship baseline → diagnosis → rerun → verification | Shows setup and skips live workflow | Same gate |
| [`04_offline_replay_and_audit`](../notebooks/04_offline_replay_and_audit.ipynb) | Deterministic replay, manifest check, in-memory tamper demonstration | Fully offline | None |

Live notebook cells spend Token Factory credits when enabled. Notebook 04 is the best first notebook because it requires no API key or network call. No notebook needs a GPU on the local computer. See [examples](examples.md), [artifacts](artifacts.md), and [security and privacy](security-and-privacy.md).
