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
from models.recipe import (
    RecipePatchRequest,
    VariationCreateRequest,
    VariationPatchRequest,
)


def get_fqdn(path: str) -> str:
    recipe_api_port: str | None = getenv("RECIPE_API_PORT")
    if recipe_api_port is None:
        raise Exception("RECIPE_API_PORT is not set")

    return f"http://localhost:{recipe_api_port}{path}"


@pytest.fixture(scope="module")
def request_headers(bearer_token: str) -> dict[str, Any]:
    return {"Authorization": f"Bearer {bearer_token}"}


def get_bearer_token(id: int) -> str:
    secret: str | None = getenv(_secret_environment_variable)
    assert secret is not None

    claims: dict[str, Any] = {
        "id": id,
        "expiry": int(time.time()) + 5000,
    }
    token: str = encode(claims, key=secret, algorithm=_bearer_token_algorithms[0])

    return token


@pytest_asyncio.fixture(scope="module")
async def bearer_token(bearer_token_user_id) -> str:
    return get_bearer_token(bearer_token_user_id)


@pytest_asyncio.fixture(scope="module")
async def unauthorized_request_headers(bearer_token_user_id) -> dict[str, Any]:
    new_bearer_token: str = get_bearer_token(bearer_token_user_id + 1)
    return {"Authorization": f"Bearer {new_bearer_token}"}


async def verify_recipe(
    http_session: aiohttp.ClientSession,
    request_headers: dict[str, Any],
    created_recipe_resource_location: str,
    expected_recipe_data: dict[str, Any],
    created_recipe_id: int,
    start_timestamp_ms: int | None = None,
) -> None:
    response: aiohttp.ClientResponse = await http_session.get(
        get_fqdn(created_recipe_resource_location), headers=request_headers
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


@pytest.fixture(scope="module")
def bearer_token_user_id() -> int:
    return 7151312342214518


@pytest.mark.asyncio
async def test_health_200(http_session: aiohttp.ClientSession) -> None:
    response: aiohttp.ClientResponse = await http_session.get(get_fqdn("/health"))
    assert 200 == response.status


@pytest.mark.asyncio
async def test_recipe_created(
    http_session: aiohttp.ClientSession,
    request_headers: dict[str, Any],
    created_recipe_resource_location: str,
    test_recipe_data: dict[str, Any],
    created_recipe_id: int,
    start_timestamp_ms: int,
) -> None:
    await verify_recipe(
        http_session,
        request_headers,
        created_recipe_resource_location,
        test_recipe_data,
        created_recipe_id,
        start_timestamp_ms,
    )


@pytest.mark.asyncio
async def test_recipe_get_404(
    http_session: aiohttp.ClientSession, request_headers: dict[str, Any]
) -> None:
    response: aiohttp.ClientResponse = await http_session.get(
        get_fqdn(f"/recipe/999999999"), headers=request_headers
    )
    assert 404 == response.status


@pytest.mark.asyncio
async def test_recipe_post_422_missing_name(
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
async def test_recipe_post_422_invalid_description(
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
async def test_recipe_post_422_invalid_name(
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
async def test_recipe_patch_204(
    http_session: aiohttp.ClientSession,
    request_headers: dict[str, Any],
    created_recipe_resource_location: str,
    created_recipe_id: int,
) -> None:
    expected_recipe_data: dict[str, Any] = {
        "description": "my updated description",
    }
    recipe_patch_request: RecipePatchRequest = RecipePatchRequest(
        **expected_recipe_data
    )
    response: aiohttp.ClientResponse = await http_session.patch(
        get_fqdn(created_recipe_resource_location),
        json=recipe_patch_request.dict(),
        headers=request_headers,
    )
    assert 204 == response.status
    modified_recipe_resource_location: str | None = response.headers.get(
        "Location", None
    )
    assert modified_recipe_resource_location is not None

    await verify_recipe(
        http_session,
        request_headers,
        modified_recipe_resource_location,
        expected_recipe_data,
        created_recipe_id,
    )


@pytest.fixture(scope="module")
def test_variation_data(created_recipe_id) -> dict[str, Any]:
    return {
        "recipe_id": created_recipe_id,
        "name": "test name",
        "ingredients": ["soy sauce", "chicken thighs", "rice"],
        "process": "do it like this",
        "notes": "it was awful",
    }


@pytest_asyncio.fixture(scope="module")
async def created_variation_resource_location(
    http_session: aiohttp.ClientSession,
    test_variation_data: dict[str, Any],
    request_headers: str,
) -> str:
    variation_create_request: VariationCreateRequest = VariationCreateRequest(
        **test_variation_data
    )
    response: aiohttp.ClientResponse = await http_session.post(
        get_fqdn("/variation"),
        json=variation_create_request.dict(),
        headers=request_headers,
    )

    assert 201 == response.status

    return response.headers["Location"]


@pytest_asyncio.fixture(scope="module")
async def created_variation_id(created_variation_resource_location: str) -> int:
    return int(created_variation_resource_location.split("/")[-1])


async def verify_variation(
    http_session: aiohttp.ClientSession,
    request_headers: dict[str, Any],
    created_variation_resource_location: str,
    expected_variation_data: dict[str, Any],
    created_variation_id: int,
    start_timestamp_ms: int | None = None,
) -> None:
    response: aiohttp.ClientResponse = await http_session.get(
        get_fqdn(created_variation_resource_location),
        headers=request_headers,
    )
    response_json: dict[Any, Any] = await response.json()

    assert 200 == response.status
    assert created_variation_id == response_json["id"]
    for key in expected_variation_data:
        assert expected_variation_data[key] == response_json[key]
    if start_timestamp_ms:
        assert (
            start_timestamp_ms < response_json["created_at"] < start_timestamp_ms + 5000
        )


@pytest.mark.asyncio
async def test_variation_created(
    http_session: aiohttp.ClientSession,
    request_headers: dict[str, Any],
    created_variation_resource_location: str,
    test_variation_data: dict[str, Any],
    created_variation_id: int,
    start_timestamp_ms: int,
) -> None:
    await verify_variation(
        http_session,
        request_headers,
        created_variation_resource_location,
        test_variation_data,
        created_variation_id,
        start_timestamp_ms,
    )


@pytest.mark.asyncio
async def test_variation_post_422_missing_name(
    http_session: aiohttp.ClientSession,
    test_variation_data: dict[str, Any],
    request_headers: dict[str, Any],
) -> None:
    del test_variation_data["name"]
    response: aiohttp.ClientResponse = await http_session.post(
        get_fqdn("/variation"),
        json=test_variation_data,
        headers=request_headers,
    )

    assert 422 == response.status


@pytest.mark.asyncio
async def test_variation_post_422_missing_recipe_id(
    http_session: aiohttp.ClientSession,
    test_variation_data: dict[str, Any],
    request_headers: dict[str, Any],
) -> None:
    del test_variation_data["recipe_id"]
    response: aiohttp.ClientResponse = await http_session.post(
        get_fqdn("/variation"),
        json=test_variation_data,
        headers=request_headers,
    )

    assert 422 == response.status


@pytest.mark.asyncio
async def test_variation_patch_204(
    http_session: aiohttp.ClientSession,
    test_variation_data: dict[str, Any],
    request_headers: dict[str, Any],
    created_variation_resource_location: str,
    created_variation_id: int,
) -> None:
    expected_variation_data: dict[str, Any] = {
        "name": "my updated name",
        "ingredients": ["rice", "egg", "msg", "white pepper"],
        "process": test_variation_data["process"],
        "notes": test_variation_data["notes"],
    }
    variation_patch_request: VariationPatchRequest = VariationPatchRequest(
        name=expected_variation_data["name"],
        ingredients=expected_variation_data["ingredients"],
    )
    response: aiohttp.ClientResponse = await http_session.patch(
        get_fqdn(created_variation_resource_location),
        json=variation_patch_request.dict(),
        headers=request_headers,
    )

    assert 204 == response.status
    modified_variation_resource_location: str | None = response.headers.get(
        "Location", None
    )
    assert modified_variation_resource_location is not None

    response: aiohttp.ClientResponse = await http_session.get(
        get_fqdn(modified_variation_resource_location), headers=request_headers
    )

    await verify_recipe(
        http_session,
        request_headers,
        modified_variation_resource_location,
        expected_variation_data,
        created_variation_id,
    )


@pytest.mark.asyncio
async def test_variation_patch_403(
    http_session: aiohttp.ClientSession,
    created_variation_resource_location: str,
    created_variation_id: int,
    unauthorized_request_headers: int,
) -> None:
    expected_variation_data: dict[str, Any] = {
        "id": created_variation_id,
        "name": "my updated name",
    }
    variation_patch_request: VariationPatchRequest = VariationPatchRequest(
        name=expected_variation_data["name"],
    )
    response: aiohttp.ClientResponse = await http_session.patch(
        get_fqdn(created_variation_resource_location),
        json=variation_patch_request.dict(),
        headers=unauthorized_request_headers,
    )
    assert 403 == response.status


@pytest.mark.asyncio
async def test_variation_delete_403(
    http_session: aiohttp.ClientSession,
    created_variation_resource_location: str,
    unauthorized_request_headers: dict[str, Any],
) -> None:
    response: aiohttp.ClientResponse = await http_session.delete(
        get_fqdn(created_variation_resource_location),
        headers=unauthorized_request_headers,
    )

    assert 403 == response.status


@pytest.mark.asyncio
async def test_variation_delete_204_404(
    http_session: aiohttp.ClientSession,
    created_variation_resource_location: str,
    request_headers: dict[str, Any],
) -> None:
    response: aiohttp.ClientResponse = await http_session.delete(
        get_fqdn(created_variation_resource_location), headers=request_headers
    )

    assert 204 == response.status

    response: aiohttp.ClientResponse = await http_session.get(
        get_fqdn(created_variation_resource_location), headers=request_headers
    )
    assert 404 == response.status


@pytest.mark.asyncio
async def test_recipe_delete_204_404(
    http_session: aiohttp.ClientSession,
    created_recipe_resource_location: str,
    request_headers: dict[str, Any],
) -> None:
    response: aiohttp.ClientResponse = await http_session.delete(
        get_fqdn(created_recipe_resource_location), headers=request_headers
    )

    assert 204 == response.status

    response: aiohttp.ClientResponse = await http_session.get(
        get_fqdn(created_recipe_resource_location),
        headers=request_headers,
    )
    assert 404 == response.status
