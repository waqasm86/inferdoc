from __future__ import annotations

import json
import os
from pathlib import Path
from typing import TYPE_CHECKING, Any

from ..evidence.models import EvidenceBundle
from ..evidence.provenance import canonical_sha256

if TYPE_CHECKING:
    from ..doctor.models import DiagnosisReport
    from ..experiments.models import ExperimentSpec
    from ..verification.verifier import VerificationReport


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
        path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        (directory / "audit.json").write_text(
            json.dumps(
                {"run_id": bundle.run_id, "evidence_sha256": canonical_sha256(payload)},
                indent=2,
            )
            + "\n",
            encoding="utf-8",
        )
        return path

    def load(self, run_id: str) -> EvidenceBundle:
        return EvidenceBundle.model_validate_json(
            (self.root / run_id / "evidence.json").read_text(encoding="utf-8")
        )

    def save_diagnosis(self, report: DiagnosisReport, run_id: str) -> Path:
        return self._save_model(run_id, "diagnosis.json", report)

    def save_experiment(self, experiment: ExperimentSpec, run_id: str) -> Path:
        return self._save_model(run_id, "experiment.json", experiment)

    def save_verification(self, report: VerificationReport, run_id: str) -> Path:
        return self._save_model(run_id, "verification.json", report)

    def _save_model(self, run_id: str, name: str, value: object) -> Path:
        directory = self.root / run_id
        directory.mkdir(parents=True, exist_ok=True)
        path = directory / name
        payload = value.model_dump(mode="json")  # type: ignore[attr-defined]
        path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        return path

    def list_runs(self) -> list[str]:
        if not self.root.exists():
            return []
        return sorted(p.name for p in self.root.iterdir() if p.is_dir())
