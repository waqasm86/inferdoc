from __future__ import annotations

from enum import StrEnum
from typing import Any

from pydantic import BaseModel, Field, model_validator


class MetricDirection(StrEnum):
    MAXIMIZE = "maximize"
    MINIMIZE = "minimize"


class MetricRule(BaseModel):
    metric: str
    direction: MetricDirection
    minimum_relative_change: float = 0.0
    maximum_relative_regression: float | None = None


class Constraint(BaseModel):
    metric: str
    maximum: float | None = None
    minimum: float | None = None

    @model_validator(mode="after")
    def one_bound(self) -> Constraint:
        if self.maximum is None and self.minimum is None:
            raise ValueError("constraint needs maximum or minimum")
        if self.maximum is not None and self.minimum is not None:
            raise ValueError("constraint cannot have both maximum and minimum")
        return self


class ExperimentSpec(BaseModel):
    id: str
    hypothesis: str
    backend: str = "nebius-token-factory"
    model: str
    baseline_run_id: str
    changed_variables: dict[str, Any] = Field(min_length=1)
    controlled_variables: dict[str, Any] = Field(min_length=1)
    objective: str
    verification_metrics: list[MetricRule] = Field(min_length=1)
    constraints: list[Constraint] = Field(default_factory=list)
    rationale: str
