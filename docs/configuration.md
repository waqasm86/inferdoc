# Configuration

`InferDocSettings.from_env(**overrides)` reads the process environment and a local `.env` without replacing already exported values. Explicit non-`None` keyword overrides take precedence. `require_api_key()` raises `ConfigurationError` only when a live call needs a missing key. `normalized_base_url()` ensures one trailing slash.

| Setting | Environment variable | Default | Required? | Purpose |
| --- | --- | --- | --- | --- |
| `api_key` | `NEBIUS_API_KEY` | `None` | Live calls only | Token Factory authentication. Offline replay and unit tests do not need it. |
| `base_url` | `INFERDOC_BASE_URL` | `https://api.tokenfactory.nebius.com/v1/` | No | OpenAI-compatible endpoint base URL. |
| `default_model` | `INFERDOC_MODEL` | `nvidia/NVIDIA-Nemotron-3-Nano-30B-A3B` | No | Default workload inference model. |
| `doctor_model` | `INFERDOC_DOCTOR_MODEL` | `nvidia/NVIDIA-Nemotron-3-Nano-30B-A3B` | No | Model requested for Doctor reasoning. |
| `timeout_s` | `INFERDOC_TIMEOUT_S` | `120.0` | No | HTTP client timeout in seconds. |
| `max_retries` | `INFERDOC_MAX_RETRIES` | `2` | No | Additional attempts for connection errors and non-streaming 5xx responses. |
| `artifact_dir` | `INFERDOC_ARTIFACT_DIR` | `.inferdoc/runs` | No | Local JSON artifact root. |

```python
from inferdoc import InferDocSettings

settings = InferDocSettings.from_env(artifact_dir="my-runs")
print(settings.default_model)
```

`INFERDOC_RUN_LIVE_TESTS` is a **test/example opt-in gate**, not an `InferDocSettings` field. Normal tests should run with it unset or `0`. Live tests and gated examples require it to equal `1` as well as a key; ordinary `inferdoc chat` and `bench` commands use the key without this gate. A malformed numeric timeout or retry environment value raises a conversion error when settings load. Avoid printing settings objects or environment values in shared logs.

See [security and privacy](security-and-privacy.md) and the placeholder-only [`.env.example`](../.env.example).
