"""Replay sanitized evidence and verify its manifest without network access."""

from __future__ import annotations

import json
from pathlib import Path

from inferdoc.evidence.models import EvidenceBundle
from inferdoc.experiments.models import ExperimentSpec
from inferdoc.storage import ArtifactStore
from inferdoc.verification import VerificationReport, verify


def replay(directory: Path) -> dict:
    baseline = EvidenceBundle.model_validate_json((directory / "baseline.json").read_text(encoding="utf-8"))
    candidate = EvidenceBundle.model_validate_json((directory / "candidate.json").read_text(encoding="utf-8"))
    experiment = ExperimentSpec.model_validate_json((directory / "experiment.json").read_text(encoding="utf-8"))
    recorded = VerificationReport.model_validate_json((directory / "verification.json").read_text(encoding="utf-8"))
    report = verify(baseline=baseline, candidate=candidate, experiment=experiment)
    integrity = ArtifactStore(directory.parent).verify_manifest(directory.name)
    return {
        "manifest_valid": integrity.valid,
        "missing": integrity.missing,
        "changed": integrity.changed,
        "verification_status": report.status,
        "recorded_status_matches": report.status == recorded.status,
        "metric_results": [result.model_dump(mode="json") for result in report.metric_results],
    }


def main() -> int:
    result = replay(Path(__file__).resolve().parent / "demo_artifacts")
    print(json.dumps(result, indent=2))
    return 0 if result["manifest_valid"] and result["recorded_status_matches"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
