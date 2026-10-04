# Command-line interface

Install the package, then run `inferdoc --help` or `python3.11 -m inferdoc.cli --help`. Commands use `InferDocSettings.from_env`; see [configuration](configuration.md). `chat`, `bench`, and `closed-loop` make live Token Factory calls and spend credits. `runs` and `validate` work locally.

| Command | Arguments and options | Behavior |
| --- | --- | --- |
| `inferdoc chat PROMPT` | `--model MODEL`, `--max-tokens N` (default 64) | Sends one non-streaming chat request and prints text. |
| `inferdoc bench PROMPT [PROMPT ...]` | `--model`, `--concurrency N` (default 1), `--max-tokens N` (64), `--stream`, `--artifact-dir PATH` | Runs one request per prompt, stores evidence, prints run ID, evidence path, and aggregate JSON. Concurrency/max tokens must be positive. |
| `inferdoc closed-loop` | Repeated `--prompt TEXT` and/or `--prompts-file PATH`; `--model`, `--concurrency N` (1), `--max-tokens N` (64), `--temperature FLOAT` (0.0), `--stream`, `--enable-thinking`, `--artifact-dir PATH` | Runs baseline, Doctor, admission, optional candidate, verification; prints a JSON summary. Prompt file uses one nonblank prompt per line. |
| `inferdoc runs` | `--artifact-dir PATH` | Lists local run-directory names, one per line. |
| `inferdoc validate EXPERIMENT.json` | Required `--baseline BASELINE.json` | Parses typed JSON, checks Token Factory admission, prints an `AdmissionDecision`. Does not contact Token Factory. |

Examples:

```bash
inferdoc runs
inferdoc validate examples/demo_artifacts/experiment.json --baseline examples/demo_artifacts/baseline.json
# Live calls below require NEBIUS_API_KEY and spend Token Factory credits.
inferdoc chat "Define TTFT." --max-tokens 32
inferdoc bench "Define TTFT." "Define throughput." --concurrency 2
inferdoc closed-loop --prompt "Define TTFT." --prompt "Define throughput."
```

For `closed-loop`, exit `0` means workflow completion, including measured FAIL, INCONCLUSIVE, or no executable recommendation; exit `2` means a proposed experiment was rejected by deterministic admission; caught runtime failures return `1`. `validate` returns `0` for approval and `2` for rejection. Argparse usage errors return `2`; errors outside the `closed-loop` catch may produce a traceback and nonzero exit. Exit status is therefore distinct from `VerificationStatus`.

`bench --stream` can observe TTFT when a content chunk arrives; its current streaming path does not retain token usage. Default non-streaming can retain usage but has no TTFT. See [benchmarking](benchmarking.md), [closed loop](closed-loop.md), and [troubleshooting](troubleshooting.md).
