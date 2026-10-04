# Local artifacts and integrity

`ArtifactStore(root=".inferdoc/runs", store_prompts=False)` writes human-readable JSON locally. `root` can be set in code, with `INFERDOC_ARTIFACT_DIR`, or with CLI `--artifact-dir` where supported. A normal run directory is `.inferdoc/runs/<run_id>/`.

| File | Created by | Contents |
| --- | --- | --- |
| `evidence.json` | `save(bundle)` | Run identity, workload, per-request measurements, aggregate, capabilities, provenance |
| `audit.json` | `save(bundle)` | Run ID and canonical evidence SHA-256 |
| `diagnosis.json` | `save_diagnosis(...)` | Typed Doctor report |
| `experiment.json` | `save_experiment(...)` | Typed proposal (saved after admission by the workflow) |
| `verification.json` | `save_verification(...)` | Candidate result |
| `manifest.json` | Save operations | Schema/run IDs, artifact names, kinds, canonical JSON SHA-256 hashes, optional baseline/candidate/experiment relations |

Baseline and candidate have separate run directories. A run without an executable proposal may have no candidate or verification. `link_closed_loop(...)` writes matching relation IDs to both manifests. JSON files are replaced atomically on the local filesystem; a manifest update itself is not a multi-file transaction.

```python
from inferdoc.storage import ArtifactStore

store = ArtifactStore()
print(store.list_runs())
result = store.verify_manifest("YOUR_RUN_ID")
print(result.valid, result.missing, result.changed)
```

`verify_manifest` recomputes canonical JSON SHA-256 for listed artifacts and reports missing or changed files. It does not repair them or prove that data came from the provider. SHA-256 is integrity detection, not encryption or an authenticity signature. The manifest itself is checked for structure and run ID but is not externally signed.

By default `save` sets each stored request's `prompt` to `null` and replaces the workload prompt list with count and SHA-256 hashes. `ArtifactStore(store_prompts=True)` explicitly retains raw prompts. Other fields such as error strings, model responses incorporated into a diagnosis, and user-provided free text may still contain sensitive data; review files before sharing. Artifacts remain on local disk until you remove them. See [security and privacy](security-and-privacy.md).
