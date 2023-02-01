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
from models.recipe import RecipePatchRequest


def get_fqdn(path: str) -> str:
    recipe_api_port: str | None = getenv("RECIPE_API_PORT")
    if recipe_api_port is None:
        raise Exception("RECIPE_API_PORT is not set")

    return f"http://localhost:{recipe_api_port}{path}"


@pytest.fixture(scope="module")
def request_headers(bearer_token: str) -> dict[str, Any]:
    return {"Authorization": f"Bearer {bearer_token}"}


async def verify_recipe(
    http_session: aiohttp.ClientSession,
    created_recipe_resource_location: str,
    expected_recipe_data: dict[str, Any],
    created_recipe_id: int,
    start_timestamp_ms: int | None = None,
) -> None:
    response: aiohttp.ClientResponse = await http_session.get(
        get_fqdn(created_recipe_resource_location)
    )
    response_json: dict[Any, Any] = await response.json()

    assert 200 == response.status
    assert created_recipe_id == response_json["id"]
    if "name" in expected_recipe_data:
        assert expected_recipe_data["name"] == response_json["name"]
    if "description" in expected_recipe_data:
        assert expected_recipe_data["description"] == response_json["description"]
    if start_timestamp_ms:
        assert (
            start_timestamp_ms < response_json["created_at"] < start_timestamp_ms + 5000
        )


@pytest.fixture(scope="module")
def test_recipe_data() -> dict[str, Any]:
    return {
        "name": "test name",
        "description": "my recipe description",
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
async def created_recipe_resource_location(
    http_session: aiohttp.ClientSession,
    test_recipe_data: dict[str, Any],
    request_headers: str,
) -> str:
    response: aiohttp.ClientResponse = await http_session.post(
        get_fqdn("/recipe"), json=test_recipe_data, headers=request_headers
    )

    assert 201 == response.status

    return response.headers["Location"]


@pytest_asyncio.fixture(scope="module")
async def created_recipe_id(created_recipe_resource_location: str) -> int:
    return int(created_recipe_resource_location.split("/")[-1])


bearer_token_user_id: int = 7151312342214518


@pytest_asyncio.fixture(scope="module")
async def bearer_token() -> str:
    secret: str | None = getenv(_secret_environment_variable)
    assert secret is not None

    claims: dict[str, Any] = {
        "id": bearer_token_user_id,
        "expiry": int(time.time()) + 5000,
    }
    token: str = encode(claims, key=secret, algorithm=_bearer_token_algorithms[0])

    return token


@pytest.mark.asyncio
async def test_health_200(http_session: aiohttp.ClientSession) -> None:
    response: aiohttp.ClientResponse = await http_session.get(get_fqdn("/health"))
    assert 200 == response.status


@pytest.mark.asyncio
async def test_recipe_created(
    http_session: aiohttp.ClientSession,
    created_recipe_resource_location: str,
    test_recipe_data: dict[str, Any],
    created_recipe_id: int,
    start_timestamp_ms: int,
) -> None:
    await verify_recipe(
        http_session,
        created_recipe_resource_location,
        test_recipe_data,
        created_recipe_id,
        start_timestamp_ms,
    )


@pytest.mark.asyncio
async def test_get_404(http_session: aiohttp.ClientSession) -> None:
    response: aiohttp.ClientResponse = await http_session.get(
        get_fqdn(f"/recipe/999999999")
    )
    assert 404 == response.status


@pytest.mark.asyncio
async def test_post_422_missing_name(
    http_session: aiohttp.ClientSession,
    test_recipe_data: dict[str, Any],
    request_headers: dict[str, Any],
) -> None:
    del test_recipe_data["name"]
    response: aiohttp.ClientResponse = await http_session.post(
        get_fqdn("/recipe"),
        json=test_recipe_data,
        headers=request_headers,
    )

    assert 422 == response.status


@pytest.mark.asyncio
async def test_post_422_invalid_description(
    http_session: aiohttp.ClientSession,
    test_recipe_data: dict[str, Any],
    request_headers: dict[str, Any],
) -> None:
    test_recipe_data["description"] = "a" * 1001
    response: aiohttp.ClientResponse = await http_session.post(
        get_fqdn("/recipe"),
        json=test_recipe_data,
        headers=request_headers,
    )

    assert 422 == response.status


@pytest.mark.asyncio
async def test_post_422_invalid_name(
    http_session: aiohttp.ClientSession,
    test_recipe_data: dict[str, Any],
    request_headers: dict[str, Any],
) -> None:
    test_recipe_data["name"] = "a" * 101
    response: aiohttp.ClientResponse = await http_session.post(
        get_fqdn("/recipe"), json=test_recipe_data, headers=request_headers
    )

    assert 422 == response.status


@pytest.mark.asyncio
async def test_patch_204(
    http_session: aiohttp.ClientSession,
    request_headers: dict[str, Any],
    created_recipe_id: int,
) -> None:
    expected_recipe_data: dict[str, Any] = {
        "id": created_recipe_id,
        "description": "my updated description",
    }
    recipe_patch_request: RecipePatchRequest = RecipePatchRequest(
        **expected_recipe_data
    )
    response: aiohttp.ClientResponse = await http_session.patch(
        get_fqdn("/recipe"),
        json=recipe_patch_request.dict(),
        headers=request_headers,
    )
    modified_recipe_resource_location: str | None = response.headers.get(
        "Location", None
    )
    assert modified_recipe_resource_location is not None
    assert 204 == response.status

    response: aiohttp.ClientResponse = await http_session.get(
        get_fqdn(modified_recipe_resource_location)
    )

    await verify_recipe(
        http_session,
        modified_recipe_resource_location,
        expected_recipe_data,
        created_recipe_id,
    )


@pytest.mark.asyncio
async def test_delete_204(
    http_session: aiohttp.ClientSession,
    created_recipe_resource_location: str,
    request_headers: dict[str, Any],
) -> None:
    response: aiohttp.ClientResponse = await http_session.delete(
        get_fqdn(created_recipe_resource_location), headers=request_headers
    )

    assert 204 == response.status

    response: aiohttp.ClientResponse = await http_session.get(
        get_fqdn(created_recipe_resource_location)
    )

    response: aiohttp.ClientResponse = await http_session.get(
        get_fqdn(created_recipe_resource_location)
    )
    assert 404 == response.status
