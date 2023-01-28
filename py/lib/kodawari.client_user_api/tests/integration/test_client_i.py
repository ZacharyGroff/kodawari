import asyncio
import time
from os import getenv
from typing import Any, AsyncIterator

import aiohttp
import pytest
import pytest_asyncio
from authentication.authentication import (
    _bearer_token_algorithms,
    _secret_environment_variable,
)
from jwt import encode
from models.user import UserCreateRequest, UserPatchRequest, UserSchema

from client_user_api.client import Client, ResponseMeta


@pytest.fixture(scope="module")
def event_loop():
    return asyncio.new_event_loop()


@pytest.fixture(scope="module")
def user_create_request() -> UserCreateRequest:
    return UserCreateRequest(display_name="testuser", description="my test description")


@pytest_asyncio.fixture(scope="module")
async def client() -> AsyncIterator[Client]:
    async with aiohttp.ClientSession() as session:
        yield Client(session, "http://localhost:8042")  # TODO: extract baseurl


@pytest_asyncio.fixture(scope="module")
async def created_user_id(
    client: Client, user_create_request: UserCreateRequest
) -> str:
    response_meta: ResponseMeta = await client.create_user(user_create_request)
    assert 201 == response_meta.status_code

    return response_meta.headers["Location"].split("/")[-1]


@pytest_asyncio.fixture(scope="module")
async def bearer_token(created_user_id: int) -> str:
    secret: str | None = getenv(_secret_environment_variable)
    assert secret is not None

    claims: dict[str, Any] = {"id": created_user_id, "expiry": int(time.time()) + 5000}
    token: str = encode(claims, key=secret, algorithm=_bearer_token_algorithms[0])

    return token


@pytest.fixture(scope="module")
def start_timestamp_ms() -> int:
    return int(time.time()) * 1000


async def verify_user(
    client: Client,
    expected_user_schema: UserSchema,
) -> None:
    actual_user_schema: UserSchema | None
    response_meta: ResponseMeta
    response_meta, actual_user_schema = await client.get_user(expected_user_schema.id)

    assert 200 == response_meta.status_code
    assert actual_user_schema is not None
    assert expected_user_schema.id == actual_user_schema.id
    assert expected_user_schema.display_name == actual_user_schema.display_name
    assert expected_user_schema.description == actual_user_schema.description
    assert expected_user_schema.joined < actual_user_schema.joined


@pytest.mark.asyncio
async def test_get_health_200(client: Client) -> None:
    response: ResponseMeta = await client.get_health()
    assert 200 == response.status_code


@pytest.mark.asyncio
async def test_user_created(
    client: Client,
    user_create_request: UserCreateRequest,
    created_user_id: int,
    start_timestamp_ms: int,
) -> None:
    expected_user_schema: UserSchema = UserSchema(
        id=created_user_id,
        display_name=user_create_request.display_name,
        description=user_create_request.description,
        joined=start_timestamp_ms,
    )
    await verify_user(client, expected_user_schema)


@pytest.mark.asyncio
async def test_patch(
    client: Client, created_user_id: int, start_timestamp_ms: int, bearer_token: str
) -> None:
    expected_display_name: str = "mynewname"
    expected_description: str = "my new description"
    user_patch_request: UserPatchRequest = UserPatchRequest(
        display_name=expected_display_name, description=expected_description
    )
    response_meta: ResponseMeta = await client.patch_user(
        user_patch_request=user_patch_request, bearer_token=bearer_token
    )

    assert 204 == response_meta.status_code

    expected_user_schema: UserSchema = UserSchema(
        id=created_user_id,
        display_name=expected_display_name,
        description=expected_description,
        joined=start_timestamp_ms,
    )
    await verify_user(client, expected_user_schema)


@pytest.mark.asyncio
async def test_delete(client: Client, created_user_id: int, bearer_token: str) -> None:
    response_meta: ResponseMeta = await client.delete_user(
        created_user_id, bearer_token
    )
    assert 204 == response_meta.status_code

    response_meta, _ = await client.get_user(created_user_id)
    assert 404 == response_meta.status_code
