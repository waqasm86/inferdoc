from __future__ import annotations

import json
from collections.abc import Callable
from typing import Any

from ..evidence.models import EvidenceBundle
from ..experiments.policy import BackendCapabilities


def tool_definitions() -> list[dict[str, Any]]:
    return [
        {
            "type": "function",
            "function": {
                "name": "get_run_summary",
                "description": "Return deterministic aggregate facts and workload configuration.",
                "parameters": {
                    "type": "object",
                    "properties": {},
                    "additionalProperties": False,
                },
            },
        },
        {
            "type": "function",
            "function": {
                "name": "get_request_metrics",
                "description": (
                    "Return deterministic per-request measurements and missing metric notes."
                ),
                "parameters": {
                    "type": "object",
                    "properties": {},
                    "additionalProperties": False,
                },
            },
        },
        {
            "type": "function",
            "function": {
                "name": "get_backend_capabilities",
                "description": "Return controls and observables exposed by the backend.",
                "parameters": {
                    "type": "object",
                    "properties": {},
                    "additionalProperties": False,
                },
            },
        },
    ]


def deterministic_tools(
    bundle: EvidenceBundle,
    capabilities: BackendCapabilities,
) -> dict[str, Callable[[], dict[str, Any]]]:
    missing = [] if any(request.ttft_s is not None for request in bundle.requests) else ["ttft_s"]
    return {
        "get_run_summary": lambda: {
            "run_id": bundle.run_id,
            "model": bundle.model,
            "backend": bundle.backend,
            "aggregate": bundle.aggregate,
            "parameters": bundle.parameters,
            "workload": bundle.workload,
        },
        "get_request_metrics": lambda: {
            "requests": [request.model_dump(mode="json") for request in bundle.requests],
            "missing_metrics": missing,
        },
        "get_backend_capabilities": lambda: capabilities.model_dump(mode="json"),
    }


def tool_result_json(value: dict[str, Any]) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True)
