from typing import Literal

from pydantic import BaseModel, ConfigDict, Field,field_validator


class TaskCandidate(BaseModel):
    model_config = ConfigDict(
        str_strip_whitespace=True,
        extra="forbid",
    )

    title: str = Field(min_length=1, max_length=100)
    priority: Literal["low", "normal", "high"] = "normal"
    tags:list[str]=Field(default_factory=list)
    description: str=Field(
        default="",
        max_length=500,
    )

    @field_validator("tags",mode="after")
    @classmethod
    def normalize_tags(
        cls,
        tags:list[str],
    )->list[str]:

        cleaned_tags = []

        for tag in tags:
            cleaned_tag=tag.strip().lower()
            if not cleaned_tag:
                raise ValueError("tags must not be empty")

            if cleaned_tag not in cleaned_tags:
                cleaned_tags.append(cleaned_tag)

        return cleaned_tags