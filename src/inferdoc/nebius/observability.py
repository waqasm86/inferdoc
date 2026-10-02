"""Optional observability boundary for hosted and dedicated Nebius backends."""

from __future__ import annotations

from datetime import datetime
from typing import Protocol

from pydantic import BaseModel, Field


class ObservabilitySnapshot(BaseModel):
    """External metrics normalized without pretending absent fields are zero."""

    source: str
    window_start: datetime
    window_end: datetime
    metrics: dict[str, float | None] = Field(default_factory=dict)
    labels: dict[str, str] = Field(default_factory=dict)


class ObservabilityAdapter(Protocol):
    def query(self, *, endpoint: str, window: str) -> ObservabilitySnapshot: ...


class UnsupportedObservabilityAdapter:
    """Explicit placeholder for serverless Token Factory, which has no GPU metrics API."""

    def query(self, *, endpoint: str, window: str) -> ObservabilitySnapshot:
        raise NotImplementedError(
            "Token Factory request evidence does not expose dedicated-endpoint GPU metrics; "
            "install an optional adapter for a documented observability source."
        )
