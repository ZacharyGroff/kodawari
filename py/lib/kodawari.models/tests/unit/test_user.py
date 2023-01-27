from typing import Any

from pydantic import ValidationError
from pytest import fixture, raises

from models.user import UserCreateRequest, UserPatchRequest, UserSchema


@fixture
def expected_user_schema() -> dict[str, Any]:
    return {
        "id": 42,
        "display_name": "testuser",
        "description": "My test description",
        "joined": 1674484829054,
    }


def test_user_schema_success(expected_user_schema) -> None:
    user_schema: UserSchema = UserSchema(**expected_user_schema)

    assert expected_user_schema["id"] == user_schema.id
    assert expected_user_schema["display_name"] == user_schema.display_name
    assert expected_user_schema["description"] == user_schema.description
    assert expected_user_schema["joined"] == user_schema.joined


def test_user_schema_id_field_must_be_positive(expected_user_schema) -> None:
    expected_user_schema["id"] = -1
    with raises(ValidationError):
        _: UserSchema = UserSchema(**expected_user_schema)


def test_user_schema_id_field_is_required(expected_user_schema) -> None:
    del expected_user_schema["id"]
    with raises(ValidationError):
        _: UserSchema = UserSchema(**expected_user_schema)


def test_user_schema_display_name_is_required(expected_user_schema) -> None:
    del expected_user_schema["display_name"]
    with raises(ValidationError):
        _: UserSchema = UserSchema(**expected_user_schema)


def test_user_schema_display_name_must_be_at_least_4_characters(
    expected_user_schema,
) -> None:
    expected_user_schema["display_name"] = "123"
    with raises(ValidationError):
        _: UserSchema = UserSchema(**expected_user_schema)


def test_user_schema_display_name_must_be_less_than_13_characters(
    expected_user_schema,
) -> None:
    expected_user_schema["display_name"] = "1234567890123"
    with raises(ValidationError):
        _: UserSchema = UserSchema(**expected_user_schema)


def test_user_schema_display_name_must_be_alphanumeric(expected_user_schema) -> None:
    expected_user_schema["display_name"] = "abcd%"
    with raises(ValidationError):
        _: UserSchema = UserSchema(**expected_user_schema)


def test_user_schema_description_defaults_to_empty_string(expected_user_schema) -> None:
    del expected_user_schema["description"]
    user_schema: UserSchema = UserSchema(**expected_user_schema)
    assert user_schema.description == ""


def test_user_schema_description_must_be_less_than_1000_characters(
    expected_user_schema,
) -> None:
    expected_user_schema["description"] = "a" * 1001
    with raises(ValidationError):
        _: UserSchema = UserSchema(**expected_user_schema)


def test_user_schema_joined_must_be_greater_than_kodawari_epoch(
    expected_user_schema,
) -> None:
    expected_user_schema["joined"] = 1674484829053
    with raises(ValidationError):
        _: UserSchema = UserSchema(**expected_user_schema)


def test_user_schema_joined_must_be_less_than_14_digits(
    expected_user_schema,
) -> None:
    expected_user_schema["joined"] = 16744848290590
    with raises(ValidationError):
        _: UserSchema = UserSchema(**expected_user_schema)


@fixture
def expected_user_create_request() -> dict[str, Any]:
    return {"display_name": "test_user", "description": "my original description"}


def test_user_create_request_success(expected_user_create_request) -> None:
    user_create_request: UserCreateRequest = UserCreateRequest(
        **expected_user_create_request
    )
    assert (
        expected_user_create_request["display_name"] == user_create_request.display_name
    )
    assert (
        expected_user_create_request["description"] == user_create_request.description
    )


def test_user_create_request_display_name_is_required(
    expected_user_create_request,
) -> None:
    del expected_user_create_request["display_name"]
    with raises(ValidationError):
        _: UserCreateRequest = UserCreateRequest(**expected_user_create_request)


def test_user_create_request_display_must_be_at_least_4_characters(
    expected_user_create_request,
) -> None:
    expected_user_create_request["display_name"] = "123"
    with raises(ValidationError):
        _: UserCreateRequest = UserCreateRequest(**expected_user_create_request)


def test_user_create_request_display_must_be_less_than_13_characters(
    expected_user_create_request,
) -> None:
    expected_user_create_request["display_name"] = "1234567890123"
    with raises(ValidationError):
        _: UserCreateRequest = UserCreateRequest(**expected_user_create_request)


def test_user_create_request_display_name_must_be_alphanumeric(
    expected_user_create_request,
) -> None:
    expected_user_create_request["display_name"] = "abc%"
    with raises(ValidationError):
        _: UserCreateRequest = UserCreateRequest(**expected_user_create_request)


def test_user_create_request_description_defaults_to_empty_string(
    expected_user_create_request,
) -> None:
    del expected_user_create_request["description"]
    user_create_request: UserCreateRequest = UserCreateRequest(
        **expected_user_create_request
    )
    assert "" == user_create_request.description


def test_user_create_request_description_must_be_less_than_1000_characters(
    expected_user_create_request,
) -> None:
    expected_user_create_request["description"] = "a" * 1001
    with raises(ValidationError):
        _: UserCreateRequest = UserCreateRequest(**expected_user_create_request)


@fixture
def expected_user_patch_request() -> dict[str, Any]:
    return {"display_name": "test_user", "description": "my original description"}


def test_user_patch_request_success(expected_user_patch_request) -> None:
    user_patch_request: UserPatchRequest = UserPatchRequest(
        **expected_user_patch_request
    )

    assert (
        expected_user_patch_request["display_name"] == user_patch_request.display_name
    )
    assert expected_user_patch_request["description"] == user_patch_request.description


def test_user_patch_request_all_fields_are_noneable(
    expected_user_patch_request,
) -> None:
    expected_user_patch_request["description"] = None
    del expected_user_patch_request["display_name"]

    user_patch_request: UserPatchRequest = UserPatchRequest(
        **expected_user_patch_request
    )

    assert user_patch_request.display_name is None
    assert user_patch_request.description is None


def test_user_patch_request_display_must_be_at_least_4_characters(
    expected_user_patch_request,
) -> None:
    expected_user_patch_request["display_name"] = "123"
    with raises(ValidationError):
        _: UserPatchRequest = UserPatchRequest(**expected_user_patch_request)


def test_user_patch_request_display_must_be_less_than_13_characters(
    expected_user_patch_request,
) -> None:
    expected_user_patch_request["display_name"] = "1234567890123"
    with raises(ValidationError):
        _: UserPatchRequest = UserPatchRequest(**expected_user_patch_request)


def test_user_patch_request_display_name_must_be_alphanumeric(
    expected_user_patch_request,
) -> None:
    expected_user_patch_request["display_name"] = "abc%"
    with raises(ValidationError):
        _: UserPatchRequest = UserPatchRequest(**expected_user_patch_request)


def test_user_patch_request_description_defaults_to_none(
    expected_user_patch_request,
) -> None:
    del expected_user_patch_request["description"]
    user_patch_request: UserPatchRequest = UserPatchRequest(
        **expected_user_patch_request
    )
    assert user_patch_request.description is None


def test_user_patch_request_description_must_be_less_than_1000_characters(
    expected_user_patch_request,
) -> None:
    expected_user_patch_request["description"] = "a" * 1001
    with raises(ValidationError):
        _: UserPatchRequest = UserPatchRequest(**expected_user_patch_request)
