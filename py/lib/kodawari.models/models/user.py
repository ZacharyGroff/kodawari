from typing import Optional

from pydantic import BaseModel, Field, validator


def display_name_must_be_alphanumeric_or_underscore(display_name: str) -> str:
    if display_name.replace("_", "").isalnum():
        return display_name
    raise ValueError("display_name must be alphanumeric")


_display_name_field = Field(
    min_length=4,
    max_length=12,
    description="The display name of a user, not required to be unique",
)
_description_field = Field(
    max_length=1000,
    default="",
    description="The user provided description for their profile",
)


class UserSchema(BaseModel):
    id: int = Field(gt=0, description="The unique identifier for a user")
    display_name: str = _display_name_field
    description: str = _description_field
    joined: int = Field(
        gt=1673984672,
        lt=9999999999,
        description="The date a user was created, expressed as a unix timestamp",
    )

    _validate_display_name = validator("display_name", allow_reuse=True)(
        display_name_must_be_alphanumeric_or_underscore
    )


class UserCreateRequest(BaseModel):
    display_name: str = _display_name_field
    description: str = _description_field

    _validate_display_name = validator("display_name", allow_reuse=True)(
        display_name_must_be_alphanumeric_or_underscore
    )


class UserPatchRequest(BaseModel):
    display_name: Optional[str] = _display_name_field
    description: Optional[str] = _description_field

    _validate_display_name = validator("display_name", allow_reuse=True)(
        display_name_must_be_alphanumeric_or_underscore
    )
