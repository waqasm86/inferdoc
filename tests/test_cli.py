import json

import pytest

from inferdoc.cli import _parser, main
from inferdoc.config import InferDocSettings
from inferdoc.doctor.models import DiagnosisReport
from inferdoc.experiments.policy import AdmissionDecision
from inferdoc.verification.verifier import VerificationReport, VerificationStatus
from inferdoc.workflows import ClosedLoopResult
from test_policy_verification import experiment


@pytest.mark.parametrize("command", [[], ["chat"], ["bench"], ["closed-loop"]])
def test_help(command, capsys):
    with pytest.raises(SystemExit) as exc:
        _parser().parse_args([*command, "--help"])
    assert exc.value.code == 0
    assert "usage:" in capsys.readouterr().out


@pytest.mark.parametrize("flag", ["--concurrency", "--max-tokens"])
def test_invalid_positive_controls(flag):
    with pytest.raises(SystemExit) as exc:
        _parser().parse_args(["closed-loop", "--prompt", "one", flag, "0"])
    assert exc.value.code == 2


def test_missing_prompts():
    with pytest.raises(SystemExit) as exc:
        main(["closed-loop"])
    assert exc.value.code == 2


def test_closed_loop_options_parse():
    args = _parser().parse_args([
        "closed-loop", "--prompt", "one", "--stream", "--enable-thinking",
        "--temperature", "0.5", "--concurrency", "2", "--max-tokens", "32",
    ])
    assert args.stream and args.enable_thinking
    assert (args.temperature, args.concurrency, args.max_tokens) == (0.5, 2, 32)


@pytest.mark.parametrize("approved,status,expected_exit", [
    (True, VerificationStatus.PASS, 0),
    (True, VerificationStatus.FAIL, 0),
    (True, VerificationStatus.INCONCLUSIVE, 0),
    (False, None, 2),
])
def test_closed_loop_cli_summary_and_forwarding(
    monkeypatch, tmp_path, evidence, capsys, approved, status, expected_exit
):
    calls = []
    prompts_file = tmp_path / "prompts.txt"
    prompts_file.write_text("second\n\nthird\n", encoding="utf-8")
    settings = InferDocSettings(api_key="fake-test-key", artifact_dir=str(tmp_path / "runs"))
    monkeypatch.setattr("inferdoc.cli.InferDocSettings.from_env", lambda **kw: settings)

    class Client:
        def __init__(self, **kwargs):
            calls.append(kwargs)

        async def aclose(self):
            calls.append("closed")

    monkeypatch.setattr("inferdoc.nebius.client.NebiusClient", Client)

    async def fake_run(**kwargs):
        calls.append(kwargs)
        exp = experiment(evidence.run_id, {"concurrency": 2})
        diagnosis = DiagnosisReport(recommendation_summary="test", experiment=exp)
        admission = AdmissionDecision(approved=approved, experiment_id=exp.id)
        candidate = evidence.model_copy(deep=True) if approved else None
        if candidate:
            candidate.run_id = "candidate"
        verification = (
            VerificationReport(status=status, baseline_run_id=evidence.run_id,
                               candidate_run_id="candidate", experiment_id=exp.id)
            if status else None
        )
        return ClosedLoopResult(baseline=evidence, diagnosis=diagnosis,
                                admission=admission, candidate=candidate,
                                verification=verification)

    monkeypatch.setattr("inferdoc.workflows.run_closed_loop", fake_run)
    code = main(["closed-loop", "--prompt", "first", "--prompt", "fourth",
                 "--prompts-file", str(prompts_file), "--artifact-dir", str(tmp_path / "runs")])
    assert code == expected_exit
    options = calls[1]
    assert options["workload"].prompts == ["first", "fourth", "second", "third"]
    assert options["workload"].stream is False
    assert options["workload"].enable_thinking is False
    assert options["artifact_store"].root == tmp_path / "runs"
    assert calls[-1] == "closed"
    summary = json.loads(capsys.readouterr().out)
    assert summary["baseline_run_id"] == evidence.run_id
    assert summary["admission_approved"] is approved
    assert summary["verification_status"] == status


def test_closed_loop_without_experiment_is_valid(monkeypatch, evidence, capsys):
    monkeypatch.setattr("inferdoc.cli.InferDocSettings.from_env",
                        lambda **kw: InferDocSettings(api_key="fake-test-key"))

    class Client:
        def __init__(self, **kwargs):
            pass

        async def aclose(self):
            pass

    async def no_experiment(**kwargs):
        return ClosedLoopResult(
            baseline=evidence, diagnosis=DiagnosisReport(recommendation_summary="none")
        )

    monkeypatch.setattr("inferdoc.nebius.client.NebiusClient", Client)
    monkeypatch.setattr("inferdoc.workflows.run_closed_loop", no_experiment)
    assert main(["closed-loop", "--prompt", "one"]) == 0
    assert json.loads(capsys.readouterr().out)["verification_status"] is None


def test_prompts_file_alone_and_runtime_failure(monkeypatch, tmp_path, capsys):
    path = tmp_path / "prompts.txt"
    path.write_text("one\ntwo\n", encoding="utf-8")
    monkeypatch.setattr("inferdoc.cli.InferDocSettings.from_env",
                        lambda **kw: InferDocSettings(api_key="fake-test-key"))

    class BrokenClient:
        def __init__(self, **kwargs):
            pass

        async def aclose(self):
            pass

    async def fail(**kwargs):
        assert kwargs["workload"].prompts == ["one", "two"]
        raise RuntimeError("synthetic failure")

    monkeypatch.setattr("inferdoc.nebius.client.NebiusClient", BrokenClient)
    monkeypatch.setattr("inferdoc.workflows.run_closed_loop", fail)
    assert main(["closed-loop", "--prompts-file", str(path)]) == 1
    assert "RuntimeError" in capsys.readouterr().err
