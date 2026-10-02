# Contributing

Use Python 3.11 or newer. Install the project directly with
`python3.11 -m pip install -e ".[dev]"` and run
`python3.11 -m compileall -q src examples tests` plus
`INFERDOC_RUN_LIVE_TESTS=0 python3.11 -m pytest -q` from this directory. Do not create or commit virtual
environments, credentials, model artifacts, or live benchmark output.

Unit tests must mock Token Factory. Mark billable tests with the `integration`
marker and require `INFERDOC_RUN_LIVE_TESTS=1`.
