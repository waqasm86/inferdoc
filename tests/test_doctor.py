import asyncio
import json

from inferdoc.doctor.agent import DoctorAgent
from inferdoc.nebius.models import ChatResponse


class FakeDoctor:
    def __init__(
        self,
        final: dict,
        *,
        tool_rounds: int = 1,
        fenced_final: bool = False,
        invalid_final: dict | None = None,
    ) -> None:
        self.calls = 0
        self.final = final
        self.tool_rounds = tool_rounds
        self.fenced_final = fenced_final
        self.invalid_final = invalid_final
        self.invalid_sent = False
        self.kwargs: list[dict] = []

    async def achat(self, **kwargs):
        self.calls += 1
        self.kwargs.append(kwargs)

        if self.calls <= self.tool_rounds:
            names = [
                "get_run_summary",
                "get_request_metrics",
                "get_backend_capabilities",
            ]
            name = names[(self.calls - 1) % len(names)]
            return ChatResponse(
                raw={
                    "choices": [
                        {
                            "message": {
                                "role": "assistant",
                                "content": None,
                                "tool_calls": [
                                    {
                                        "id": f"call-{self.calls}",
                                        "type": "function",
                                        "function": {"name": name, "arguments": "{}"},
                                    }
                                ],
                            }
                        }
                    ]
                }
            )

        payload = self.final
        if self.invalid_final is not None and not self.invalid_sent:
            payload = self.invalid_final
            self.invalid_sent = True

        text = json.dumps(payload)
        if self.fenced_final:
            text = f"```json\n{text}\n```"

        return ChatResponse(
            text=text,
            finish_reason="stop",
            raw={
                "choices": [
                    {
                        "finish_reason": "stop",
                        "message": {"role": "assistant", "content": text},
                    }
                ]
            },
        )


def _valid_experiment(evidence) -> dict:
    return {
        "measured_facts": ["Two requests completed."],
        "derived_facts": ["Output throughput is measured by Python."],
        "hypotheses": ["Concurrency may improve overlap."],
        "missing_evidence": [],
        "recommendation_summary": "Try concurrency two.",
        "experiment": {
            "id": "exp-1",
            "hypothesis": "Concurrency increases throughput.",
            "model": evidence.model,
            "baseline_run_id": evidence.run_id,
            "changed_variables": {"concurrency": 2},
            "controlled_variables": {
                "max_tokens": 16,
                "temperature": 0.0,
                "stream": False,
            },
            "objective": "increase throughput",
            "verification_metrics": [
                {
                    "metric": "output_token_throughput_tps",
                    "direction": "maximize",
                    "minimum_relative_change": 0.01,
                }
            ],
            "constraints": [],
            "rationale": "small controlled test",
        },
    }


def _live_shape_invalid(evidence) -> dict:
    return {
        "measured_facts": {
            "run_id": evidence.run_id,
            "backend": evidence.backend,
        },
        "derived_facts": {"low_concurrency_likely": True},
        "hypotheses": ["Concurrency may improve throughput."],
        "missing_evidence": ["TTFT is unavailable."],
        "recommendation_summary": "Increase concurrency and rerun.",
        "experiment": {
            "concurrency": 8.0,
            "description": "Test higher concurrency while keeping other parameters unchanged.",
        },
    }


def test_doctor_uses_tools_and_returns_typed_experiment(evidence) -> None:
    fake = FakeDoctor(_valid_experiment(evidence), tool_rounds=1)
    report = asyncio.run(DoctorAgent(fake).adiagnose(evidence))

    assert report.experiment is not None
    assert fake.calls == 2
    first = fake.kwargs[0]
    assert first["temperature"] == 0.6
    assert first["top_p"] == 0.95
    assert first["max_tokens"] == 4096
    assert first["tool_choice"] == "auto"
    assert first["chat_template_kwargs"] == {"enable_thinking": True}


def test_doctor_parses_fenced_nested_json(evidence) -> None:
    fake = FakeDoctor(_valid_experiment(evidence), tool_rounds=1, fenced_final=True)
    report = asyncio.run(DoctorAgent(fake).adiagnose(evidence))

    assert report.experiment is not None
    assert report.experiment.changed_variables["concurrency"] == 2


def test_doctor_allows_final_synthesis_after_three_tool_rounds(evidence) -> None:
    fake = FakeDoctor(_valid_experiment(evidence), tool_rounds=3)
    report = asyncio.run(DoctorAgent(fake, max_tool_rounds=3).adiagnose(evidence))

    assert report.experiment is not None
    assert fake.calls == 4
    for call in fake.kwargs[:3]:
        assert call["tool_choice"] == "auto"
        assert "tools" in call

    final_call = fake.kwargs[3]
    assert "tools" not in final_call
    assert "tool_choice" not in final_call
    assert final_call["chat_template_kwargs"] == {"enable_thinking": True}
    assert len(report.audit_log) == 3
    assert [entry["tool"] for entry in report.audit_log] == [
        "get_run_summary",
        "get_request_metrics",
        "get_backend_capabilities",
    ]


def test_doctor_repairs_live_style_schema_mismatch(evidence) -> None:
    fake = FakeDoctor(
        _valid_experiment(evidence),
        tool_rounds=3,
        invalid_final=_live_shape_invalid(evidence),
    )
    report = asyncio.run(
        DoctorAgent(fake, max_tool_rounds=3, max_schema_repairs=2).adiagnose(evidence)
    )

    assert report.experiment is not None
    assert report.experiment.changed_variables == {"concurrency": 2}
    assert fake.calls == 5
    repair_call = fake.kwargs[-1]
    assert "tools" not in repair_call
    assert "tool_choice" not in repair_call
    repair_text = repair_call["messages"][-1]["content"]
    assert "Pydantic validation errors" in repair_text
    assert "measured_facts" in repair_text
    assert "complete ExperimentSpec" in repair_text or "ExperimentSpec" in repair_text


def test_doctor_rejects_impossible_control(evidence) -> None:
    final = {
        "measured_facts": [],
        "derived_facts": [],
        "hypotheses": [],
        "missing_evidence": [],
        "recommendation_summary": "Try TP2.",
        "experiment": {
            "id": "exp-unsupported",
            "hypothesis": "TP2 helps",
            "model": evidence.model,
            "baseline_run_id": evidence.run_id,
            "changed_variables": {"tensor_parallel_size": 2},
            "controlled_variables": {"max_tokens": 16},
            "objective": "increase throughput",
            "verification_metrics": [
                {"metric": "output_token_throughput_tps", "direction": "maximize"}
            ],
            "constraints": [],
            "rationale": "unsupported example",
        },
    }

    report = asyncio.run(DoctorAgent(FakeDoctor(final)).adiagnose(evidence))
    assert report.experiment is None
    assert any("tensor_parallel_size" in item for item in report.missing_evidence)


def test_run_summary_tool_exposes_baseline_workload(evidence) -> None:
    from inferdoc.doctor.tools import deterministic_tools
    from inferdoc.experiments.capabilities import DEMO_TOKEN_FACTORY_CAPABILITIES

    tools = deterministic_tools(evidence, DEMO_TOKEN_FACTORY_CAPABILITIES)
    summary = tools["get_run_summary"]()

    assert summary["workload"]["concurrency"] == 1
    assert summary["workload"]["max_tokens"] == 16
    assert summary["parameters"]["stream"] is False
