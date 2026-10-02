from __future__ import annotations

import asyncio
import json
import re
from typing import Any

from pydantic import ValidationError

from ..evidence.models import EvidenceBundle
from ..evidence.provenance import canonical_sha256
from ..experiments.capabilities import TOKEN_FACTORY_CAPABILITIES
from ..experiments.policy import BackendCapabilities, validate_experiment
from ..nebius.client import NebiusClient
from .models import DiagnosisReport
from .prompts import SYSTEM_PROMPT, finalization_prompt, repair_prompt, user_prompt
from .tools import deterministic_tools, tool_definitions, tool_result_json


def _json_from_text(text: str) -> dict[str, Any]:
    text = text.strip()
    if not text:
        raise ValueError("doctor response did not contain JSON")

    fenced = re.search(
        r"```(?:json)?\s*(.*?)\s*```",
        text,
        re.DOTALL | re.IGNORECASE,
    )
    if fenced:
        candidate = fenced.group(1).strip()
    else:
        start = text.find("{")
        end = text.rfind("}")
        if start == -1 or end == -1 or end < start:
            raise ValueError("doctor response did not contain a JSON object")
        candidate = text[start : end + 1]

    try:
        parsed = json.loads(candidate)
    except json.JSONDecodeError as exc:
        raise ValueError("doctor response contained invalid JSON") from exc

    if not isinstance(parsed, dict):
        raise ValueError("doctor response JSON must be an object")
    return parsed


class DoctorAgent:
    """Bounded Nemotron reasoning loop over deterministic read-only evidence tools.

    ``max_tool_rounds`` limits tool-bearing model turns. A separate synthesis turn is
    always available after the tool budget, and schema-invalid synthesis output can be
    repaired with bounded no-tool turns.
    """

    def __init__(
        self,
        client: Any | None = None,
        *,
        capabilities: BackendCapabilities | None = None,
        max_tool_rounds: int = 3,
        max_schema_repairs: int = 2,
    ) -> None:
        if max_tool_rounds < 1:
            raise ValueError("max_tool_rounds must be at least 1")
        if max_schema_repairs < 0:
            raise ValueError("max_schema_repairs must be non-negative")

        self._owns_client = client is None
        self.client = client or NebiusClient()
        self.capabilities = capabilities or TOKEN_FACTORY_CAPABILITIES
        self.max_tool_rounds = max_tool_rounds
        self.max_schema_repairs = max_schema_repairs

    async def _call_model(
        self,
        *,
        bundle: EvidenceBundle,
        messages: list[dict[str, Any]],
        allow_tools: bool,
    ) -> Any:
        kwargs: dict[str, Any] = {
            "model": getattr(
                getattr(self.client, "settings", None),
                "doctor_model",
                bundle.model,
            ),
            "messages": messages,
            "temperature": 0.6,
            "top_p": 0.95,
            "max_tokens": 4096,
            "chat_template_kwargs": {"enable_thinking": True},
        }
        if allow_tools:
            kwargs["tools"] = tool_definitions()
            kwargs["tool_choice"] = "auto"
        return await self.client.achat(**kwargs)

    @staticmethod
    def _assistant_message(response: Any) -> dict[str, Any]:
        raw = getattr(response, "raw", {}) or {}
        choices = raw.get("choices") or [{}]
        message = choices[0].get("message") or {}
        return message if isinstance(message, dict) else {}

    def _admit_report(
        self,
        *,
        bundle: EvidenceBundle,
        report: DiagnosisReport,
        audit: list[dict[str, Any]],
    ) -> DiagnosisReport:
        if report.experiment is not None:
            decision = validate_experiment(
                report.experiment,
                self.capabilities,
                baseline=bundle,
                max_changed_variables=1,
            )
            if not decision.approved:
                report.missing_evidence.extend(decision.reasons)
                report.experiment = None
                report.recommendation_summary += (
                    " Deterministic admission rejected the proposed experiment."
                )

        report.audit_log = audit
        bundle.provenance["doctor_audit"] = audit
        return report

    async def _parse_or_repair_report(
        self,
        *,
        bundle: EvidenceBundle,
        response: Any,
        messages: list[dict[str, Any]],
        audit: list[dict[str, Any]],
        stage: str,
    ) -> DiagnosisReport:
        current_response = response
        current_messages = list(messages)
        last_error: Exception | None = None
        last_parsed: dict[str, Any] | None = None

        for repair_index in range(self.max_schema_repairs + 1):
            final_text = getattr(current_response, "text", "")
            try:
                parsed = _json_from_text(final_text)
                last_parsed = parsed
                report = DiagnosisReport.model_validate(parsed)
                return self._admit_report(bundle=bundle, report=report, audit=audit)
            except (ValueError, ValidationError) as exc:
                last_error = exc
                if repair_index >= self.max_schema_repairs:
                    break

                if last_parsed is None:
                    # The response was not valid JSON. Preserve it as a diagnostic object so
                    # Nemotron can repair syntax without InferDoc inventing semantic content.
                    invalid_json: dict[str, Any] = {"raw_text": final_text}
                else:
                    invalid_json = last_parsed

                validation_errors = str(exc)
                assistant_message = self._assistant_message(current_response)
                if assistant_message:
                    current_messages.append(assistant_message)
                elif final_text:
                    current_messages.append({"role": "assistant", "content": final_text})

                current_messages.append(
                    {
                        "role": "user",
                        "content": repair_prompt(
                            bundle=bundle,
                            invalid_json=invalid_json,
                            validation_errors=validation_errors,
                        ),
                    }
                )
                current_response = await self._call_model(
                    bundle=bundle,
                    messages=current_messages,
                    allow_tools=False,
                )
                last_parsed = None

        raise ValueError(
            "Nemotron returned an invalid DiagnosisReport after bounded schema repair. "
            f"stage={stage}; repairs={self.max_schema_repairs}; "
            f"finish_reason={getattr(current_response, 'finish_reason', None)!r}; "
            f"final_text={getattr(current_response, 'text', '')!r}; "
            f"reasoning_content={getattr(current_response, 'reasoning_content', None)!r}; "
            f"tool_audit={audit!r}; error={last_error}"
        ) from last_error

    async def adiagnose(self, bundle: EvidenceBundle) -> DiagnosisReport:
        tools = deterministic_tools(bundle, self.capabilities)
        messages: list[dict[str, Any]] = [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt(bundle.run_id)},
        ]
        audit: list[dict[str, Any]] = []

        for round_index in range(self.max_tool_rounds):
            response = await self._call_model(
                bundle=bundle,
                messages=messages,
                allow_tools=True,
            )
            assistant_message = self._assistant_message(response)
            tool_calls = assistant_message.get("tool_calls") or []

            if not tool_calls:
                return await self._parse_or_repair_report(
                    bundle=bundle,
                    response=response,
                    messages=messages,
                    audit=audit,
                    stage=f"tool_round_{round_index}",
                )

            messages.append(assistant_message)
            for call in tool_calls:
                function = call.get("function", {}) or {}
                name = function.get("name")
                fn = tools.get(name)
                result = fn() if fn else {"error": f"unknown read-only tool {name}"}

                raw_arguments = function.get("arguments") or "{}"
                try:
                    arguments = json.loads(raw_arguments)
                except (TypeError, json.JSONDecodeError):
                    arguments = {"raw": raw_arguments}

                audit.append(
                    {
                        "round": round_index,
                        "tool": name,
                        "call_id": call.get("id"),
                        "arguments": arguments,
                        "result_sha256": canonical_sha256(result),
                    }
                )
                messages.append(
                    {
                        "role": "tool",
                        "tool_call_id": call.get("id"),
                        "content": tool_result_json(result),
                    }
                )

        messages.append(
            {
                "role": "user",
                "content": finalization_prompt(bundle),
            }
        )
        response = await self._call_model(
            bundle=bundle,
            messages=messages,
            allow_tools=False,
        )
        if self._assistant_message(response).get("tool_calls"):
            raise ValueError(
                "Nemotron attempted a tool call during forced finalization; "
                f"tool_audit={audit!r}"
            )

        return await self._parse_or_repair_report(
            bundle=bundle,
            response=response,
            messages=messages,
            audit=audit,
            stage="forced_finalization",
        )

    def diagnose(self, bundle: EvidenceBundle) -> DiagnosisReport:
        async def _run_once() -> DiagnosisReport:
            try:
                return await self.adiagnose(bundle)
            finally:
                if self._owns_client and hasattr(self.client, "aclose"):
                    await self.client.aclose()

        return asyncio.run(_run_once())


def diagnose(
    bundle: EvidenceBundle,
    *,
    client: Any | None = None,
) -> DiagnosisReport:
    return DoctorAgent(client).diagnose(bundle)
