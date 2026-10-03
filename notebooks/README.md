# InferDoc notebooks

These notebooks import the installed InferDoc package. Launch ordinary
JupyterLab or Jupyter Notebook from the repository root so relative example
paths resolve. Python 3.11 is required.

```bash
python3.11 -m pip install -e ".[notebooks]"
python3.11 -m jupyter lab
```

| Notebook | Purpose | Credits |
| --- | --- | --- |
| `00_token_factory_quickstart.ipynb` | One short Token Factory call | Only with live gate |
| `01_benchmark_evidence.ipynb` | Deterministic benchmark evidence | Only with live gate; streaming second run is separately opted in |
| `02_nemotron_diagnosis.ipynb` | Read-only tools, diagnosis, policy admission | Captured evidence by default; new diagnosis is separately opted in |
| `03_closed_loop_experiment.ipynb` | Flagship complete workflow | Only with live gate |
| `04_offline_replay_and_audit.ipynb` | Replay, manifest, in-memory tamper check | Never |

For live cells, set both `INFERDOC_RUN_LIVE_TESTS=1` and `NEBIUS_API_KEY` in
the process environment. The notebooks never print the API key. Notebook 04
requires no API key or network connection. All committed code cells have
cleared outputs and execution metadata.
