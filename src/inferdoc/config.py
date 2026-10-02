from __future__ import annotations

import os
from dataclasses import dataclass

from dotenv import load_dotenv

from .exceptions import ConfigurationError


def _load_local_env() -> None:
    """Load a local .env file without overwriting exported variables."""
    load_dotenv(override=False)


@dataclass(frozen=True)
class InferDocSettings:
    api_key: str | None = None
    base_url: str = "https://api.tokenfactory.nebius.com/v1/"

    default_model: str = "nvidia/NVIDIA-Nemotron-3-Nano-30B-A3B"
    doctor_model: str = "nvidia/NVIDIA-Nemotron-3-Nano-30B-A3B"

    timeout_s: float = 120.0
    max_retries: int = 2
    artifact_dir: str = ".inferdoc/runs"

    @classmethod
    def from_env(cls, **overrides: object) -> InferDocSettings:
        _load_local_env()

        values: dict[str, object] = {
            "api_key": os.getenv("NEBIUS_API_KEY"),
            "base_url": os.getenv(
                "INFERDOC_BASE_URL",
                cls.base_url,
            ),
            "default_model": os.getenv(
                "INFERDOC_MODEL",
                cls.default_model,
            ),
            "doctor_model": os.getenv(
                "INFERDOC_DOCTOR_MODEL",
                cls.doctor_model,
            ),
            "timeout_s": float(
                os.getenv(
                    "INFERDOC_TIMEOUT_S",
                    str(cls.timeout_s),
                )
            ),
            "max_retries": int(
                os.getenv(
                    "INFERDOC_MAX_RETRIES",
                    str(cls.max_retries),
                )
            ),
            "artifact_dir": os.getenv(
                "INFERDOC_ARTIFACT_DIR",
                cls.artifact_dir,
            ),
        }

        values.update(
            {
                key: value
                for key, value in overrides.items()
                if value is not None
            }
        )

        return cls(**values)

    def require_api_key(self) -> str:
        if not self.api_key:
            raise ConfigurationError(
                "NEBIUS_API_KEY is required for live Token Factory calls; "
                "unit tests and offline evidence analysis do not need it."
            )
        return self.api_key

    def normalized_base_url(self) -> str:
        return self.base_url.rstrip("/") + "/"