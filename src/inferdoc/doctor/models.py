from __future__ import annotations

from pydantic import BaseModel, Field

from ..experiments.models import ExperimentSpec


class DiagnosisReport(BaseModel):
    measured_facts: list[str] = Field(default_factory=list)
    derived_facts: list[str] = Field(default_factory=list)
    hypotheses: list[str] = Field(default_factory=list)
    missing_evidence: list[str] = Field(default_factory=list)
    recommendation_summary: str
    experiment: ExperimentSpec | None = None
    audit_log: list[dict[str, object]] = Field(default_factory=list)
