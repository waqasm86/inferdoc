from __future__ import annotations

from pydantic import (
    BaseModel,
    Field,
    field_validator,
)


class WorkloadSpec(BaseModel):
    prompts: list[str] = Field(
        min_length=1
    )

    concurrency: int = Field(
        default=1,
        ge=1,
    )

    max_tokens: int = Field(
        default=64,
        ge=1,
    )

    temperature: float = Field(
        default=0.0,
        ge=0.0,
    )

    stream: bool = True

    enable_thinking: bool = False

    @field_validator("prompts")
    @classmethod
    def nonempty_prompts(
        cls,
        value: list[str],
    ) -> list[str]:
        if any(
            not prompt.strip()
            for prompt in value
        ):
            raise ValueError(
                "prompts must not contain "
                "empty strings"
            )

        return value
