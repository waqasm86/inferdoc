# Development

Use Python 3.11 or newer in a source checkout. The package uses a `src/` layout and setuptools. Install the existing development dependencies directly in your Python 3.11 environment if needed:

```bash
python3.11 -m pip install -e ".[dev]"
INFERDOC_RUN_LIVE_TESTS=0 python3.11 -m compileall -q src examples tests
INFERDOC_RUN_LIVE_TESTS=0 python3.11 -m pytest -q
```

Offline tests mock the provider and skip the opt-in live integration tests. Do not enable `INFERDOC_RUN_LIVE_TESTS=1` unless you intend to make billable Token Factory requests. Notebook tests inspect JSON statically; they do not execute cells. Use [example 05](../examples/05_replay_verification.py) for a no-credit artifact replay.

For a local packaging check, direct output outside the repository and never upload it as part of this check:

```bash
python3.11 -m build --no-isolation --outdir /tmp/inferdoc-build-check
python3.11 -m twine check /tmp/inferdoc-build-check/*
```

[CI](../.github/workflows/ci.yml) runs Python 3.11 compileall, pytest with the live gate at `0`, build, and Twine check. It does not currently run a separate linter. See [contributing](../CONTRIBUTING.md), [release process](release.md), and [security](security-and-privacy.md).
