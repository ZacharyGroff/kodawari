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


def get_fqdn(path: str) -> str:
    return f"http://localhost:8000{path}"


async def verify_user(
    http_session: aiohttp.ClientSession,
    resource_path: str,
    expected_user_data: dict[str, Any],
    start_timestamp_ms: int | None = None,
) -> None:
    user_id: int = int(resource_path.split("/")[-1])
    response: aiohttp.ClientResponse = await http_session.get(get_fqdn(resource_path))
    response_json: dict[Any, Any] = await response.json()

    assert 200 == response.status
    assert user_id == response_json["id"]
    if "display_name" in expected_user_data:
        assert expected_user_data["display_name"] == response_json["display_name"]
    if "description" in expected_user_data:
        assert expected_user_data["description"] == response_json["description"]
    if start_timestamp_ms:
        assert start_timestamp_ms < response_json["joined"] < start_timestamp_ms + 5000


@pytest.fixture(scope="module")
def test_user_data() -> dict[str, Any]:
    return {
        "display_name": "testuser",
        "description": "my user description",
    }


@pytest.fixture()
def start_timestamp_ms() -> int:
    return int(time.time()) * 1000


@pytest.fixture(scope="module")
def event_loop():
    return asyncio.new_event_loop()


@pytest_asyncio.fixture(scope="module")
async def http_session() -> AsyncIterator[aiohttp.ClientSession]:
    async with aiohttp.ClientSession() as session:
        yield session


@pytest_asyncio.fixture(scope="module")
async def created_user_resource_location(
    http_session: aiohttp.ClientSession, test_user_data: dict[str, Any]
) -> str:
    response: aiohttp.ClientResponse = await http_session.post(
        get_fqdn("/user"), json=test_user_data
    )

    assert 201 == response.status

    return response.headers["location"]


@pytest_asyncio.fixture(scope="module")
async def bearer_token(created_user_resource_location: str) -> str:
    secret: str | None = getenv(_secret_environment_variable)
    assert secret is not None

    created_user_id: int = int(created_user_resource_location.split("/")[-1])
    claims: dict[str, Any] = {"id": created_user_id, "expiry": int(time.time()) + 5000}
    token: str = encode(claims, key=secret, algorithm=_bearer_token_algorithms[0])

    return token


@pytest.mark.asyncio
async def test_health_200(http_session: aiohttp.ClientSession) -> None:
    response: aiohttp.ClientResponse = await http_session.get(get_fqdn("/health"))
    assert 200 == response.status


@pytest.mark.asyncio
async def test_user_created(
    http_session: aiohttp.ClientSession,
    created_user_resource_location: str,
    test_user_data: dict[str, Any],
    start_timestamp_ms: int,
) -> None:
    await verify_user(
        http_session, created_user_resource_location, test_user_data, start_timestamp_ms
    )


@pytest.mark.asyncio
async def test_post_422_missing_display_name(
    http_session: aiohttp.ClientSession, test_user_data: dict[str, Any]
) -> None:
    del test_user_data["display_name"]
    response: aiohttp.ClientResponse = await http_session.post(
        get_fqdn("/user"), json=test_user_data
    )

    assert 422 == response.status


@pytest.mark.asyncio
async def test_post_422_invalid_description(
    http_session: aiohttp.ClientSession, test_user_data: dict[str, Any]
) -> None:
    test_user_data["description"] = "a" * 1001
    response: aiohttp.ClientResponse = await http_session.post(
        get_fqdn("/user"), json=test_user_data
    )

    assert 422 == response.status


@pytest.mark.asyncio
async def test_post_422_invalid_display_name(
    http_session: aiohttp.ClientSession, test_user_data: dict[str, Any]
) -> None:
    test_user_data["display_name"] = "123"
    response: aiohttp.ClientResponse = await http_session.post(
        get_fqdn("/user"), json=test_user_data
    )

    assert 422 == response.status


@pytest.mark.asyncio
async def test_get_404(http_session: aiohttp.ClientSession) -> None:
    response: aiohttp.ClientResponse = await http_session.get(
        get_fqdn(f"/user/999999999")
    )
    assert 404 == response.status


@pytest.mark.asyncio
async def test_patch_204(
    http_session: aiohttp.ClientSession,
    bearer_token: str,
) -> None:
    expected_user_data: dict[str, Any] = {
        "description": "my updated description",
    }
    headers: dict[str, str] = {"Authorization": f"Bearer {bearer_token}"}
    response: aiohttp.ClientResponse = await http_session.patch(
        get_fqdn("/user"), json=expected_user_data, headers=headers
    )
    modified_user_resource_location: str | None = response.headers.get("location", None)
    assert modified_user_resource_location is not None
    assert 204 == response.status

    response: aiohttp.ClientResponse = await http_session.get(
        get_fqdn(modified_user_resource_location)
    )

    await verify_user(http_session, modified_user_resource_location, expected_user_data)


@pytest.mark.asyncio
async def test_delete_204(
    http_session: aiohttp.ClientSession,
    created_user_resource_location: str,
    bearer_token: str,
) -> None:
    headers: dict[str, str] = {"Authorization": f"Bearer {bearer_token}"}
    response: aiohttp.ClientResponse = await http_session.delete(
        get_fqdn("/user"), headers=headers
    )

    assert 204 == response.status

    response: aiohttp.ClientResponse = await http_session.get(
        get_fqdn(created_user_resource_location)
    )

    response: aiohttp.ClientResponse = await http_session.get(
        get_fqdn(created_user_resource_location)
    )
    assert 404 == response.status
