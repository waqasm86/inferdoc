# Release and PyPI publishing

InferDoc uses a `src/` layout, setuptools, and PyPI Trusted Publishing.

Before every release:

```bash
python3.11 -m compileall -q src examples tests
INFERDOC_RUN_LIVE_TESTS=0 python3.11 -m pytest -q
rm -rf build dist src/*.egg-info
python3.11 -m build --no-isolation
python3.11 -m twine check dist/*
```

Create a Git tag matching the package version, push it, and create a GitHub Release.
`.github/workflows/release.yml` publishes with PyPI OIDC Trusted Publishing; no
long-lived PyPI token is stored in GitHub.

Trusted Publisher values:
- Owner: `waqasm86`
- Repository: `inferdoc`
- Workflow: `release.yml`
- Environment: `pypi`
- PyPI project: `inferdoc`
