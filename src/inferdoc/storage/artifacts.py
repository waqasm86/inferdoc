from __future__ import annotations

import json
import os
import tempfile
from pathlib import Path
from typing import TYPE_CHECKING, Any

from pydantic import BaseModel, Field

from ..evidence.models import EvidenceBundle
from ..evidence.provenance import canonical_sha256

if TYPE_CHECKING:
    from ..doctor.models import DiagnosisReport
    from ..experiments.models import ExperimentSpec
    from ..verification.verifier import VerificationReport


class ManifestVerification(BaseModel):
    valid: bool
    missing: list[str] = Field(default_factory=list)
    changed: list[str] = Field(default_factory=list)


class ArtifactStore:
    """JSON run storage. Prompt text is redacted unless explicitly enabled."""

    def __init__(
        self,
        root: str | os.PathLike[str] = ".inferdoc/runs",
        *,
        store_prompts: bool = False,
    ) -> None:
        self.root = Path(root)
        self.store_prompts = store_prompts

    def _storage_payload(self, bundle: EvidenceBundle) -> dict[str, Any]:
        payload = bundle.model_dump(mode="json")
        if self.store_prompts:
            return payload
        for request in payload.get("requests", []):
            request["prompt"] = None
        workload = payload.get("workload", {})
        prompts = workload.get("prompts")
        if isinstance(prompts, list):
            workload["prompt_count"] = len(prompts)
            workload["prompt_sha256"] = [canonical_sha256(prompt) for prompt in prompts]
            workload["prompts"] = []
        return payload

    def save(self, bundle: EvidenceBundle, name: str = "evidence.json") -> Path:
        directory = self.root / bundle.run_id
        directory.mkdir(parents=True, exist_ok=True)
        path = directory / name
        payload = self._storage_payload(bundle)
        self._write_json(path, payload)
        audit = {"run_id": bundle.run_id, "evidence_sha256": canonical_sha256(payload)}
        self._write_json(directory / "audit.json", audit)
        self._update_manifest(bundle.run_id, {name: ("evidence", payload), "audit.json": ("audit", audit)})
        return path

    def load(self, run_id: str) -> EvidenceBundle:
        return EvidenceBundle.model_validate_json(
            (self.root / run_id / "evidence.json").read_text(encoding="utf-8")
        )

    def save_diagnosis(self, report: DiagnosisReport, run_id: str) -> Path:
        return self._save_model(run_id, "diagnosis.json", report)

    def save_experiment(self, experiment: ExperimentSpec, run_id: str) -> Path:
        path = self._save_model(run_id, "experiment.json", experiment)
        self._update_manifest(run_id, {}, baseline_run_id=experiment.baseline_run_id,
                              experiment_id=experiment.id)
        return path

    def save_verification(self, report: VerificationReport, run_id: str) -> Path:
        path = self._save_model(run_id, "verification.json", report)
        self._update_manifest(run_id, {}, baseline_run_id=report.baseline_run_id,
                              candidate_run_id=report.candidate_run_id,
                              experiment_id=report.experiment_id)
        return path

    def _save_model(self, run_id: str, name: str, value: object) -> Path:
        directory = self.root / run_id
        directory.mkdir(parents=True, exist_ok=True)
        path = directory / name
        payload = value.model_dump(mode="json")  # type: ignore[attr-defined]
        self._write_json(path, payload)
        self._update_manifest(run_id, {name: (name.removesuffix(".json"), payload)})
        return path

    @staticmethod
    def _write_json(path: Path, payload: dict[str, Any]) -> None:
        """Replace one JSON file atomically on the same filesystem."""
        with tempfile.NamedTemporaryFile(mode="w", encoding="utf-8", dir=path.parent,
                                         prefix=f".{path.name}.", delete=False) as handle:
            temporary = Path(handle.name)
            try:
                json.dump(payload, handle, indent=2, ensure_ascii=False)
                handle.write("\n")
                handle.flush()
                os.fsync(handle.fileno())
            except Exception:
                temporary.unlink(missing_ok=True)
                raise
        try:
            os.replace(temporary, path)
        except OSError:
            temporary.unlink(missing_ok=True)
            raise

    def _update_manifest(self, run_id: str, entries: dict[str, tuple[str, dict[str, Any]]],
                         **relations: str) -> None:
        path = self.root / run_id / "manifest.json"
        manifest = (json.loads(path.read_text(encoding="utf-8")) if path.exists() else
                    {"schema_version": "1.0", "run_id": run_id, "artifacts": {}})
        for name, (kind, payload) in entries.items():
            manifest["artifacts"][name] = {"sha256": canonical_sha256(payload), "kind": kind}
        manifest.update(relations)
        self._write_json(path, manifest)

    def link_closed_loop(self, *, baseline_run_id: str, candidate_run_id: str,
                         experiment_id: str) -> None:
        """Record the same closed-loop relation on both run manifests."""
        for run_id in (baseline_run_id, candidate_run_id):
            self._update_manifest(run_id, {}, baseline_run_id=baseline_run_id,
                                  candidate_run_id=candidate_run_id,
                                  experiment_id=experiment_id)

    def verify_manifest(self, run_id: str) -> ManifestVerification:
        directory = self.root / run_id
        path = directory / "manifest.json"
        if not path.is_file():
            return ManifestVerification(valid=False, missing=["manifest.json"])
        try:
            manifest = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            return ManifestVerification(valid=False, changed=["manifest.json"])
        if not isinstance(manifest, dict):
            return ManifestVerification(valid=False, changed=["manifest.json"])
        missing: list[str] = []
        changed: list[str] = []
        if manifest.get("schema_version") != "1.0":
            changed.append("manifest.json: unsupported schema_version")
        if manifest.get("run_id") != run_id:
            changed.append("manifest.json: run_id mismatch")
        records = manifest.get("artifacts")
        if not isinstance(records, dict):
            return ManifestVerification(valid=False, changed=["manifest.json: invalid artifacts"])
        for name, record in records.items():
            if not isinstance(name, str) or not isinstance(record, dict):
                changed.append("manifest.json: invalid artifact entry")
                continue
            if Path(name).name != name or name == "manifest.json":
                changed.append(f"invalid artifact name: {name}")
                continue
            artifact = directory / name
            if not artifact.is_file():
                missing.append(name)
                continue
            try:
                payload = json.loads(artifact.read_text(encoding="utf-8"))
            except (OSError, json.JSONDecodeError):
                changed.append(name)
                continue
            if canonical_sha256(payload) != record.get("sha256"):
                changed.append(name)
        if not records:
            changed.append("manifest.json: no artifacts")
        return ManifestVerification(valid=not missing and not changed, missing=missing, changed=changed)

    def list_runs(self) -> list[str]:
        if not self.root.exists():
            return []
        return sorted(p.name for p in self.root.iterdir() if p.is_dir())
