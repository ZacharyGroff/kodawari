from authentication import BearerClaims, BearerValidationException, SecretEnvironmentVariableException, authenticate, validate_bearer, _bearer_token_algorithms
from fastapi import HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials
from pydantic import ValidationError
from typing import Any, Dict
from unittest.mock import patch

import pytest


token: str = 'test'
secret: str = 'test_secret'


def test_validate_bearer_secret_is_none() -> None:
    with patch('authentication.getenv') as get_env_mock:
        get_env_mock.return_value = None
        with pytest.raises(SecretEnvironmentVariableException):
            validate_bearer('test')
        get_env_mock.assert_called_once()


def test_validate_bearer_token_is_expired() -> None:
    with (
            patch('authentication.decode') as decode_mock,
            patch('authentication.getenv') as get_env_mock
    ):
        get_env_mock.return_value = secret
        decode_mock.return_value = {
            'id': 42,
            'expiry': 1650001000
        }
        with pytest.raises(BearerValidationException):
            validate_bearer(token)
        get_env_mock.assert_called_once()
        decode_mock.assert_called_once_with(
            token, key=secret, algorithms=_bearer_token_algorithms)


def test_validate_bearer_token_is_malformed() -> None:
    with (
            patch('authentication.decode') as decode_mock,
            patch('authentication.getenv') as get_env_mock
    ):

        get_env_mock.return_value = secret
        decode_mock.return_value = {
            '_id': 42,
            'expiry': 1750001000
        }
        with pytest.raises(ValidationError):
            validate_bearer(token)
        get_env_mock.assert_called_once()
        decode_mock.assert_called_once_with(
            token, key=secret, algorithms=_bearer_token_algorithms)


def test_validate_bearer_success() -> None:
    with (
            patch('authentication.decode') as decode_mock,
            patch('authentication.getenv') as get_env_mock
    ):

        claims: Dict[str, Any] = {
            'id': 42,
            'expiry': 1750001000
        }
        get_env_mock.return_value = secret
        decode_mock.return_value = claims
        result: BearerClaims = validate_bearer(token)

        assert claims.get('id') == result.id
        assert claims.get('expiry') == result.expiry

        get_env_mock.assert_called_once()
        decode_mock.assert_called_once_with(
            token, key=secret, algorithms=_bearer_token_algorithms)


@pytest.mark.asyncio
async def test_validate_raises_bearer_validation_exception() -> None:
    with patch('authentication.validate_bearer') as validate_bearer_mock:
        validate_bearer_mock.side_effect = BearerValidationException(
            'fake-token')

        expected_credentials: str = 'test-credentials'
        authorization_credentials: HTTPAuthorizationCredentials = HTTPAuthorizationCredentials(
            scheme='test-scheme', credentials=expected_credentials)

        with pytest.raises(HTTPException) as ex:
            await authenticate(credentials=authorization_credentials)
            assert status.HTTP_401_UNAUTHORIZED == ex.status_code

        validate_bearer_mock.assert_called_once_with(expected_credentials)


@pytest.mark.asyncio
async def test_validation_raises_unexpected_exception() -> None:
    with patch('authentication.validate_bearer') as validate_bearer_mock:
        validate_bearer_mock.side_effect = Exception('fake exception thrown')

        expected_credentials: str = 'test-credentials'
        authorization_credentials: HTTPAuthorizationCredentials = HTTPAuthorizationCredentials(
            scheme='test-scheme', credentials=expected_credentials)

        with pytest.raises(HTTPException) as ex:
            await authenticate(credentials=authorization_credentials)
            assert status.HTTP_500_INTERNAL_SERVER_ERROR == ex.status_code

        validate_bearer_mock.assert_called_once_with(expected_credentials)


@pytest.mark.asyncio
async def test_validate_success() -> None:
    with patch('authentication.validate_bearer') as validate_bearer_mock:
        expected_credentials: str = 'test-credentials'
        authorization_credentials: HTTPAuthorizationCredentials = HTTPAuthorizationCredentials(
            scheme='test-scheme', credentials=expected_credentials)

        expected_bearer_claims: BearerClaims = BearerClaims(
            id=42, expiry=1750001000)
        validate_bearer_mock.return_value = expected_bearer_claims

        actual_bearer_claims: BearerClaims = await authenticate(credentials=authorization_credentials)

        assert expected_bearer_claims == actual_bearer_claims
        validate_bearer_mock.assert_called_once_with(expected_credentials)
