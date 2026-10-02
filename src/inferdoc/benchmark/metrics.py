from __future__ import annotations

import math
from collections.abc import Iterable
from statistics import fmean


def percentile(values: Iterable[float], p: float) -> float | None:
    """Linear-interpolated percentile; unavailable for an empty input."""
    values = sorted(float(v) for v in values if math.isfinite(float(v)))
    if not values:
        return None
    if not 0 <= p <= 100:
        raise ValueError("p must be between 0 and 100")
    position = (len(values) - 1) * p / 100
    lower, upper = math.floor(position), math.ceil(position)
    if lower == upper:
        return values[lower]
    fraction = position - lower
    return values[lower] + fraction * (values[upper] - values[lower])


def summary(values: Iterable[float]) -> dict[str, float | None]:
    values = list(values)
    return {
        "mean": fmean(values) if values else None,
        "p50": percentile(values, 50),
        "p90": percentile(values, 90),
        "p95": percentile(values, 95),
        "p99": percentile(values, 99),
    }
