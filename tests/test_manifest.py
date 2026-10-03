import json
import runpy
from pathlib import Path

import pytest

from inferdoc.doctor.models import DiagnosisReport
from inferdoc.evidence.provenance import canonical_sha256
from inferdoc.storage import ArtifactStore
from inferdoc.verification import VerificationReport, VerificationStatus
from test_policy_verification import experiment


def _populated_store(tmp_path, evidence):
    store = ArtifactStore(tmp_path)
    store.save(evidence)
    store.save_diagnosis(DiagnosisReport(recommendation_summary="test"), evidence.run_id)
    store.save_experiment(experiment(evidence.run_id, {"concurrency": 2}), evidence.run_id)
    store.save_verification(VerificationReport(
        status=VerificationStatus.PASS, baseline_run_id=evidence.run_id,
        candidate_run_id=evidence.run_id, experiment_id="exp-1",
    ), evidence.run_id)
    return store, tmp_path / evidence.run_id


def test_manifest_creation_update_and_relations(tmp_path, evidence):
    store, directory = _populated_store(tmp_path, evidence)
    manifest = json.loads((directory / "manifest.json").read_text(encoding="utf-8"))
    assert set(manifest["artifacts"]) == {
        "evidence.json", "audit.json", "diagnosis.json", "experiment.json", "verification.json"
    }
    assert manifest["baseline_run_id"] == evidence.run_id
    assert manifest["experiment_id"] == "exp-1"
    assert store.verify_manifest(evidence.run_id).valid
    for name, record in manifest["artifacts"].items():
        assert record["sha256"] == canonical_sha256(json.loads((directory / name).read_text()))


def test_manifest_hash_is_canonical_json(tmp_path, evidence):
    store, directory = _populated_store(tmp_path, evidence)
    path = directory / "diagnosis.json"
    data = json.loads(path.read_text(encoding="utf-8"))
    path.write_text(json.dumps(data, separators=(",", ":")), encoding="utf-8")
    assert store.verify_manifest(evidence.run_id).valid


@pytest.mark.parametrize("name", ["evidence.json", "diagnosis.json", "experiment.json", "verification.json"])
def test_manifest_detects_tampered_artifact(tmp_path, evidence, name):
    store, directory = _populated_store(tmp_path, evidence)
    path = directory / name
    data = json.loads(path.read_text(encoding="utf-8"))
    data["tampered"] = True
    path.write_text(json.dumps(data), encoding="utf-8")
    result = store.verify_manifest(evidence.run_id)
    assert not result.valid
    assert result.changed == [name]


def test_manifest_detects_missing_artifact(tmp_path, evidence):
    store, directory = _populated_store(tmp_path, evidence)
    (directory / "diagnosis.json").unlink()
    result = store.verify_manifest(evidence.run_id)
    assert not result.valid
    assert result.missing == ["diagnosis.json"]


def test_manifest_reports_corrupt_manifest(tmp_path, evidence):
    store, directory = _populated_store(tmp_path, evidence)
    (directory / "manifest.json").write_text("{broken", encoding="utf-8")
    result = store.verify_manifest(evidence.run_id)
    assert not result.valid
    assert result.changed == ["manifest.json"]


def test_manifest_update_does_not_erase_previous_entries(tmp_path, evidence):
    store = ArtifactStore(tmp_path)
    store.save_diagnosis(DiagnosisReport(recommendation_summary="test"), evidence.run_id)
    store.save(evidence)
    assert store.verify_manifest(evidence.run_id).valid
    data = json.loads((tmp_path / evidence.run_id / "manifest.json").read_text())
    assert "diagnosis.json" in data["artifacts"]
    assert "evidence.json" in data["artifacts"]


def test_offline_replay_and_redacted_prompts():
    root = Path(__file__).resolve().parents[1]
    demo = root / "examples" / "demo_artifacts"
    namespace = runpy.run_path(str(root / "examples" / "05_replay_verification.py"))
    result = namespace["replay"](demo)
    assert result["manifest_valid"]
    assert result["verification_status"] == VerificationStatus.PASS
    assert result["recorded_status_matches"]
    DiagnosisReport.model_validate_json((demo / "diagnosis.json").read_text(encoding="utf-8"))
    for name in ("baseline.json", "candidate.json"):
        payload = json.loads((demo / name).read_text(encoding="utf-8"))
        assert payload["workload"]["prompts"] == []
        assert all(request["prompt"] is None for request in payload["requests"])


def test_closed_loop_links_both_run_manifests(tmp_path, evidence):
    store = ArtifactStore(tmp_path)
    baseline = evidence.model_copy(deep=True)
    candidate = evidence.model_copy(deep=True)
    candidate.run_id = "candidate"
    store.save(baseline)
    store.save(candidate)
    store.link_closed_loop(
        baseline_run_id=baseline.run_id, candidate_run_id=candidate.run_id,
        experiment_id="exp-1",
    )
    for run_id in (baseline.run_id, candidate.run_id):
        manifest = json.loads((tmp_path / run_id / "manifest.json").read_text())
        assert manifest["baseline_run_id"] == baseline.run_id
        assert manifest["candidate_run_id"] == candidate.run_id
        assert manifest["experiment_id"] == "exp-1"
        assert store.verify_manifest(run_id).valid
