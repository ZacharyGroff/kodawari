from authentication import BearerClaims, authenticate, _bearer_token_algorithms, _secret_environment_variable
from fastapi import Depends, FastAPI
from fastapi.testclient import TestClient
from jwt import encode
from os import environ
from typing import Any, Dict, Generator
import pytest


@pytest.fixture(scope='module')
def fastapi_test_client() -> Generator[TestClient, None, None]:
    test_app = FastAPI()
    client = TestClient(test_app)

    @test_app.get('/', response_model=BearerClaims)
    async def get_bearer(bearer_claims: BearerClaims = Depends(authenticate)):
        return bearer_claims

    yield client


@pytest.fixture
def secret() -> Generator[str, None, None]:
    secret: str = 'a-very-secret-key'
    environ[_secret_environment_variable] = secret
    yield secret
    del environ[_secret_environment_variable]


@pytest.fixture(scope='module')
def claims() -> Generator[Dict[str, Any], None, None]:
    claims: Dict[str, Any] = {'id': 42, 'expiry': 1750003000}
    yield claims


@pytest.mark.asyncio
async def test_200_request_is_authorized(fastapi_test_client: TestClient, secret: str, claims: Dict[str, Any]) -> None:
    token: str = encode(claims, key=secret,
                        algorithm=_bearer_token_algorithms[0])
    headers: Dict[str, str] = {'Authorization': f'Bearer {token}'}

    response = fastapi_test_client.get('/', headers=headers)

    assert response.status_code == 200
    assert response.json() == claims


@pytest.mark.asyncio
async def test_401_expiry_is_in_past(fastapi_test_client: TestClient, secret: str, claims: Dict[str, Any]) -> None:
    claims['expiry'] = 0
    token: str = encode(claims, key=secret,
                        algorithm=_bearer_token_algorithms[0])
    headers: Dict[str, str] = {'Authorization': f'Bearer {token}'}

    response = fastapi_test_client.get('/', headers=headers)

    assert response.status_code == 401
    assert response.json() == {'detail': 'Unauthorized'}


@pytest.mark.asyncio
async def test_401_token_cannot_be_decoded(fastapi_test_client: TestClient, secret: str, claims: Dict[str, Any]) -> None:
    secret = 'a-fake-secret'
    token: str = encode(claims, key=secret,
                        algorithm=_bearer_token_algorithms[0])
    headers: Dict[str, str] = {'Authorization': f'Bearer {token}'}

    response = fastapi_test_client.get('/', headers=headers)

    assert response.status_code == 401
    assert response.json() == {'detail': 'Unauthorized'}


@pytest.mark.asyncio
async def test_500_secret_environment_variable_not_set(fastapi_test_client: TestClient, claims: Dict[str, Any]) -> None:
    secret: str = 'a-fake-secret'
    token: str = encode(claims, key=secret,
                        algorithm=_bearer_token_algorithms[0])
    headers: Dict[str, str] = {'Authorization': f'Bearer {token}'}

    response = fastapi_test_client.get('/', headers=headers)

    assert response.status_code == 500
    assert response.json() == {'detail': 'Internal Server Error'}
