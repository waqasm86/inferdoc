# Sanitized measured replay

These six JSON files are a sanitized example captured from one successful
Nebius Token Factory closed-loop run on 2026-10-02. The baseline used eight
short public inference-engineering prompts at concurrency 1; the admitted
experiment changed client concurrency to 2. Python verification returned
`PASS` for the measured output-token-throughput objective. The reported p95
latencies are observations, not a declared constraint. **Captured example from one live run; not a universal performance
guarantee.**

Prompt text was already redacted in the source evidence. This copy also
removes host platform metadata and the diagnosis tool call audit IDs. It
contains no API key, authorization header, local path, or raw prompt text.
The aggregate timings and token counts are retained as observed. The manifest
hashes each sanitized JSON payload after these removals.

Run `python3.11 examples/05_replay_verification.py` from the repository root.
It uses only local files and deterministic Python verification. It requires
no API key or network connection.
