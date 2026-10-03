# Public YouTube demo outline (2:55–3:00)

Use notebook `03_closed_loop_experiment.ipynb` as the flagship walkthrough,
with captured evidence ready to show so the edit stays under three minutes.
Use notebook 04 for the no-credit replay and artifact audit. If a fresh live
run ends in FAIL, INCONCLUSIVE, or no executable experiment, present that
outcome honestly; do not substitute a claimed PASS.

| Time | Scene and narration |
| --- | --- |
| 0:00–0:20 | Problem: inference changes need evidence. Show InferDoc's Nemotron-reasons, Python-verifies boundary. |
| 0:20–0:45 | Show Nebius Token Factory endpoint and NVIDIA Nemotron-3 Nano model name without displaying credentials. |
| 0:45–1:10 | Show controlled baseline workload, measured EvidenceBundle, and run-level metric availability. |
| 1:10–1:35 | Show read-only tools, Nemotron diagnosis, and one ExperimentSpec. |
| 1:35–1:55 | Show deterministic policy admission and the single changed control. |
| 1:55–2:20 | Show candidate rerun and comparable workload evidence. |
| 2:20–2:40 | Show Python's PASS/FAIL/INCONCLUSIVE report and measured metric deltas. |
| 2:40–2:55 | Show notebook 04 offline replay, SHA-256 manifest, and in-memory tamper detection. |
| 2:55–3:00 | Show GitHub and install command; close. |

Before publication, add the public YouTube URL to `docs/devpost-submission.md`.
