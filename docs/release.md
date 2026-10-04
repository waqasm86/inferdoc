# Release and PyPI publishing

InferDoc uses a `src/` layout, setuptools, and PyPI Trusted Publishing. Version 0.1.0 is already published at [PyPI](https://pypi.org/project/inferdoc/0.1.0/) and tagged [`v0.1.0`](https://github.com/waqasm86/inferdoc/releases/tag/v0.1.0); published files are immutable. Do not recreate that release or bump the version merely for website search visibility.

For a **future planned release**, update the matching versions in `pyproject.toml` and `src/inferdoc/__init__.py`, review README/package metadata and release notes, and run the offline checks from the repository root:

```bash
python3.11 -m compileall -q src examples tests
INFERDOC_RUN_LIVE_TESTS=0 python3.11 -m pytest -q
python3.11 -m build --no-isolation --outdir /tmp/inferdoc-release-check
python3.11 -m twine check /tmp/inferdoc-release-check/*
```

Inspect both archives for expected modules, README, LICENSE, and absence of `.env` or other secrets. Ensure the main CI run passes and the tag matches the committed version. Creating a published GitHub Release triggers [`.github/workflows/release.yml`](../.github/workflows/release.yml): a Python 3.11 build job transfers distributions to a publish job with environment `pypi`, `id-token: write`, and `pypa/gh-action-pypi-publish`. The PyPI Trusted Publisher is configured for owner `waqasm86`, repository `inferdoc`, workflow `release.yml`, environment `pypi`. No static PyPI token belongs in the repository.

After a future workflow succeeds, verify the direct PyPI JSON and Simple APIs, files, version, and a clean public installation. Website search is a separate index from package resolution. See [development](development.md). These instructions do not authorize a release during documentation work.
