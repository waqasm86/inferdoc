from __future__ import annotations

import json
from typing import Any

from ..evidence.models import EvidenceBundle

SYSTEM_PROMPT = """You are InferDoc Doctor, an inference engineering analyst.
Python owns measured and derived facts. You own interpretation, hypotheses,
missing evidence, and one controlled next experiment.

Rules:
- Never invent measurements, GPU facts, provider telemetry, or controls.
- Treat tool outputs as the only authoritative evidence about the run.
- Token Factory cannot accept arbitrary vLLM runtime knobs.
- Use read-only tools only when needed. You do not need to call every tool.
- After you have enough evidence, stop calling tools and return the final report.
- Return exactly one JSON object and no prose outside that JSON object.
- measured_facts, derived_facts, hypotheses, and missing_evidence MUST each be
  JSON arrays of strings, never JSON objects.
- experiment must be either a complete ExperimentSpec object or null.
- Never return a shorthand experiment such as {\"concurrency\": 8}.
- Prefer one small controlled experiment. For the demo backend, change only
  concurrency and keep all other workload variables controlled.
"""


def _controlled_variables(bundle: EvidenceBundle) -> dict[str, Any]:
    """Return the baseline workload fields that a concurrency experiment holds fixed."""
    controlled: dict[str, Any] = {}
    for name in ("max_tokens", "temperature", "stream", "enable_thinking"):
        if name in bundle.workload:
            controlled[name] = bundle.workload[name]
    return controlled


def _experiment_example(bundle: EvidenceBundle) -> dict[str, Any]:
    baseline_concurrency = bundle.workload.get("concurrency", 1)
    try:
        baseline_concurrency_int = int(baseline_concurrency)
    except (TypeError, ValueError):
        baseline_concurrency_int = 1

    candidate_concurrency = min(max(baseline_concurrency_int + 1, 2), 8)

    return {
        "id": "exp-concurrency-1",
        "hypothesis": "Higher client concurrency may increase output-token throughput.",
        "backend": bundle.backend,
        "model": bundle.model,
        "baseline_run_id": bundle.run_id,
        "changed_variables": {"concurrency": candidate_concurrency},
        "controlled_variables": _controlled_variables(bundle),
        "objective": "increase output-token throughput",
        "verification_metrics": [
            {
                "metric": "output_token_throughput_tps",
                "direction": "maximize",
                "minimum_relative_change": 0.01,
                "maximum_relative_regression": None,
            }
        ],
        "constraints": [],
        "rationale": "Run one bounded concurrency experiment while holding the workload fixed.",
    }


def finalization_prompt(bundle: EvidenceBundle) -> str:
    example = {
        "measured_facts": ["A measured fact stated as a sentence."],
        "derived_facts": ["A deterministic derived fact stated as a sentence."],
        "hypotheses": ["A hypothesis stated as a sentence."],
        "missing_evidence": ["A genuinely unavailable measurement, if any."],
        "recommendation_summary": "A concise recommendation.",
        "experiment": _experiment_example(bundle),
    }
    return (
        "Tool collection is complete. Do not call any more tools. Using only the evidence "
        "already present in this conversation, return the final DiagnosisReport as exactly one "
        "JSON object with no markdown fences and no additional prose.\n\n"
        "STRICT SHAPE REQUIREMENTS:\n"
        "- measured_facts: array of strings\n"
        "- derived_facts: array of strings\n"
        "- hypotheses: array of strings\n"
        "- missing_evidence: array of strings\n"
        "- recommendation_summary: string\n"
        "- experiment: null OR a COMPLETE ExperimentSpec with every required field\n"
        "- if experiment is not null, changed_variables must change ONLY concurrency\n"
        "- do not return measured_facts or derived_facts as objects\n"
        "- do not return a shorthand experiment\n\n"
        "Use this object only as a structural example; replace its prose and candidate value "
        "with your evidence-based conclusion:\n"
        f"{json.dumps(example, ensure_ascii=False, indent=2)}"
    )


def repair_prompt(
    *,
    bundle: EvidenceBundle,
    invalid_json: dict[str, Any],
    validation_errors: str,
) -> str:
    example = {
        "measured_facts": ["A measured fact stated as a sentence."],
        "derived_facts": ["A deterministic derived fact stated as a sentence."],
        "hypotheses": ["A hypothesis stated as a sentence."],
        "missing_evidence": ["A genuinely unavailable measurement, if any."],
        "recommendation_summary": "A concise recommendation.",
        "experiment": _experiment_example(bundle),
    }
    return (
        "Your previous JSON was syntactically valid but did not satisfy InferDoc's typed schema. "
        "Repair the SAME diagnosis; do not add new measurements and do not call tools. Return "
        "exactly one corrected JSON object with no markdown fences or prose.\n\n"
        "Pydantic validation errors:\n"
        f"{validation_errors}\n\n"
        "Invalid JSON to repair:\n"
        f"{json.dumps(invalid_json, ensure_ascii=False, indent=2)}\n\n"
        "Required structural example:\n"
        f"{json.dumps(example, ensure_ascii=False, indent=2)}\n\n"
        "Remember: all four fact/evidence fields are arrays of strings, and any non-null "
        "experiment must contain every ExperimentSpec field shown in the example."
    )


def user_prompt(run_id: str) -> str:
    return (
        f"Analyze evidence run {run_id}. Use read-only tools only as needed, then return the "
        "final DiagnosisReport JSON using the exact typed shape required by the system prompt."
    )
