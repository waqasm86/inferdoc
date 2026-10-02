from __future__ import annotations

import hashlib
import json
import platform
import sys
from typing import Any


def canonical_sha256(value: Any) -> str:
    payload = json.dumps(
        value, sort_keys=True, separators=(",", ":"), default=str, ensure_ascii=False
    ).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def runtime_provenance(
    *, workload: dict[str, Any], provider: str, endpoint_host: str, inferdoc_version: str
) -> dict[str, Any]:
    """Build non-secret runtime provenance for an evidence bundle."""
    return {
        "inferdoc_version": inferdoc_version,
        "python_version": sys.version.split()[0],
        "platform": platform.platform(),
        "provider": provider,
        "endpoint_host": endpoint_host,
        "workload_sha256": canonical_sha256(workload),
    }
