from typing import Literal

from pydantic import BaseModel
from pydantic import Field
from pydantic import field_validator


Intensity = Literal[
    "low",
    "medium",
    "high",
]


class UserInput(BaseModel):

    username: str = Field(
        min_length=2,
        max_length=100,
    )

    user_id: str = Field(
        min_length=2,
        max_length=100,
    )

    age: int = Field(
        ge=13,
        le=100,
    )

    weight: float = Field(
        gt=20,
        le=500,
    )

    goal: str = Field(
        min_length=2,
        max_length=100,
    )

    intensity: Intensity

    @field_validator(
        "username",
        "user_id",
        "goal",
    )
    @classmethod
    def clean_text(cls, value: str) -> str:

        value = value.strip()

        if not value:
            raise ValueError(
                "This field cannot be empty."
            )

        return value


class FeedbackRequest(BaseModel):

    user_id: str = Field(
        min_length=2,
        max_length=100,
    )

    feedback: str = Field(
        min_length=3,
        max_length=2000,
    )

    @field_validator(
        "user_id",
        "feedback",
    )
    @classmethod
    def clean_text(cls, value: str) -> str:

        value = value.strip()

        if not value:
            raise ValueError(
                "This field cannot be empty."
            )

        return value