from pydantic import BaseModel, Field, validator


def display_name_must_be_alphanumeric_or_underscore(display_name: str) -> str:
    if display_name.replace("_", "").isalnum():
        return display_name
    raise ValueError("display_name must be alphanumeric")


_display_name_field = Field(
    min_length=4,
    max_length=12,
    description="The non-unique alphanumeric display name of a user, restricted to a minimum of four and a maximum of twelve characters",
)
_description_field = Field(
    max_length=1000,
    default="",
    description="The user provided description for their profile, restricted to a maximum of 1000 characters, defaulting to empty string",
)


class UserSchema(BaseModel):
    """A user's profile information.

    Attributes:
        id: The unique identifier for a user
        display_name: The non-unique alphanumeric display name of a user, restricted to a minimum of 4 and a maximum of 12 characters
        description: The user provided description for their profile, restricted to a maximum of 1000 characters, defaulting to empty string
        joined: The date a user was created, expressed as a unix timestamp in milliseconds
    """

    id: int = Field(gt=0, description="The unique identifier for a user")
    display_name: str = _display_name_field
    description: str = _description_field
    joined: int = Field(
        gt=1674484829053,
        lt=9999999999999,
        description="The date a user was created, expressed as a unix timestamp in milliseconds",
    )

    _validate_display_name = validator("display_name", allow_reuse=True)(
        display_name_must_be_alphanumeric_or_underscore
    )


class UserCreateRequest(BaseModel):
    """The required request body for creating a UserSchema object

    Attributes:
        display_name: The non-unique alphanumeric display name of a user, restricted to a minimum of 4 and a maximum of 12 characters
        description: The user provided description for their profile, restricted to a maximum of 1000 characters, defaulting to empty string
    """

    display_name: str = _display_name_field
    description: str = _description_field

    _validate_display_name = validator("display_name", allow_reuse=True)(
        display_name_must_be_alphanumeric_or_underscore
    )


class UserPatchRequest(BaseModel):
    """The required request body for patching a UserSchema object

    Attributes:
        display_name: The (optional) non-unique alphanumeric display name of a user, restricted to a minimum of 4 and a maximum of 12 characters
        description: The (optional) user provided description for their profile, restricted to a maximum of 1000 characters, defaulting to empty string
    """

    display_name: str | None = _display_name_field
    description: str | None = _description_field

    _validate_display_name = validator("display_name", allow_reuse=True)(
        display_name_must_be_alphanumeric_or_underscore
    )
