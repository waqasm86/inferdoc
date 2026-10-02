import json

from inferdoc.storage import ArtifactStore


def test_artifact_round_trip_and_hash(evidence, tmp_path) -> None:
    store = ArtifactStore(tmp_path / "runs", store_prompts=True)
    path = store.save(evidence)
    loaded = store.load(evidence.run_id)
    assert path.name == "evidence.json"
    assert loaded == evidence
    assert evidence.run_id in store.list_runs()
    assert (path.parent / "audit.json").exists()


def test_artifact_store_supports_closed_loop_records(evidence, tmp_path) -> None:
    from inferdoc.doctor.models import DiagnosisReport
    from inferdoc.experiments.models import ExperimentSpec, MetricDirection, MetricRule

    store = ArtifactStore(tmp_path / "runs")
    report = DiagnosisReport(recommendation_summary="insufficient evidence")
    diagnosis_path = store.save_diagnosis(report, evidence.run_id)
    experiment = ExperimentSpec(
        id="exp",
        hypothesis="test",
        model=evidence.model,
        baseline_run_id=evidence.run_id,
        changed_variables={"concurrency": 2},
        controlled_variables={"max_tokens": 16},
        objective="throughput",
        verification_metrics=[
            MetricRule(metric="request_throughput_rps", direction=MetricDirection.MAXIMIZE)
        ],
        rationale="test",
    )
    experiment_path = store.save_experiment(experiment, evidence.run_id)
    assert diagnosis_path.exists()
    assert experiment_path.exists()


def test_store_redacts_prompts_by_default(tmp_path, evidence) -> None:
    store = ArtifactStore(tmp_path)
    path = store.save(evidence)
    payload = json.loads(path.read_text(encoding="utf-8"))
    assert all(item["prompt"] is None for item in payload["requests"])
    assert payload["workload"]["prompts"] == []
    assert payload["workload"]["prompt_count"] == 2


def test_store_can_explicitly_keep_prompts(tmp_path, evidence) -> None:
    store = ArtifactStore(tmp_path, store_prompts=True)
    path = store.save(evidence)
    payload = json.loads(path.read_text(encoding="utf-8"))
    assert payload["requests"][0]["prompt"] == "one"
    assert payload["workload"]["prompts"] == ["one", "two"]
