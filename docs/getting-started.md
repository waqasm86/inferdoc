# Getting started

InferDoc requires Python 3.11 or newer. Nebius Token Factory performs hosted inference; an API key and credits are needed only for live calls. The [offline replay](#first-offline-check) works without either.

## Install

From [PyPI](https://pypi.org/project/inferdoc/):

```bash
python3.11 -m pip install inferdoc
inferdoc --help
```

For source development from the repository root:

```bash
python3.11 -m pip install -e ".[dev]"
```

The optional `openai` and `notebooks` extras are not needed for the core SDK. See [configuration](configuration.md) for all supported settings.

## First offline check

Clone the [repository](https://github.com/waqasm86/inferdoc) for its sanitized example data, then run:

```bash
git clone https://github.com/waqasm86/inferdoc.git
cd inferdoc
python3.11 examples/05_replay_verification.py
```

This verifies the local SHA-256 manifest and replays Python verification. It makes no provider call. The script reports whether the recorded status matches the recomputed status; its captured outcome is not a performance guarantee.

## First live chat

Set `NEBIUS_API_KEY` in your own environment or a local, Git-ignored `.env`. Do not commit it. This request spends Token Factory credits:

```bash
inferdoc chat "Define TTFT in one sentence." --max-tokens 32
```

Equivalent Python call:

```python
import inferdoc

response = inferdoc.chat(prompt="Define TTFT in one sentence.", max_tokens=32)
print(response.text)
```

## First benchmark

This also makes live Token Factory requests:

```bash
inferdoc bench "Define TTFT." "Define throughput." --concurrency 2 --max-tokens 32
```

The CLI writes evidence under `.inferdoc/runs` by default. Non-streaming is the default and can retain provider token usage. `--stream` opts into TTFT observation, but current streaming evidence does not retain usage. See [benchmarking](benchmarking.md), [CLI](cli.md), and [artifacts](artifacts.md).
