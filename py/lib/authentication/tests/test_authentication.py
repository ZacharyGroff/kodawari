from authentication import BearerClaims, BearerValidationException, SecretEnvironmentVariableException, authenticate, validate_bearer, _bearer_token_algorithms, _security_scheme
from fastapi import HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials
from pydantic import ValidationError
from typing import Any, Dict
import unittest
from unittest.mock import MagicMock, patch


class TestValidateBearer(unittest.TestCase):
    token: str = 'test'
    secret: str = 'test_secret'

    @patch('authentication.getenv')
    def test_secret_is_none(self, get_env_mock: MagicMock) -> None:
        get_env_mock.return_value = None
        with self.assertRaises(SecretEnvironmentVariableException):
            validate_bearer('test')
        get_env_mock.assert_called_once()

    @patch('authentication.decode')
    @patch('authentication.getenv')
    def test_token_is_expired(self, get_env_mock: MagicMock, decode_mock: MagicMock) -> None:
        get_env_mock.return_value = self.secret
        decode_mock.return_value = {
            'id': 42,
            'expiry': 1650001000
        }
        with self.assertRaises(BearerValidationException):
            validate_bearer(self.token)
        get_env_mock.assert_called_once()
        decode_mock.assert_called_once_with(
            self.token, key=self.secret, algorithms=_bearer_token_algorithms)

    @patch('authentication.decode')
    @patch('authentication.getenv')
    def test_token_is_malformed(self, get_env_mock: MagicMock, decode_mock: MagicMock) -> None:
        get_env_mock.return_value = self.secret
        decode_mock.return_value = {
            '_id': 42,
            'expiry': 1750001000
        }
        with self.assertRaises(ValidationError):
            validate_bearer(self.token)
        get_env_mock.assert_called_once()
        decode_mock.assert_called_once_with(
            self.token, key=self.secret, algorithms=_bearer_token_algorithms)

    @patch('authentication.decode')
    @patch('authentication.getenv')
    def test_success(self, get_env_mock: MagicMock, decode_mock: MagicMock) -> None:
        claims: Dict[str, Any] = {
            'id': 42,
            'expiry': 1750001000
        }
        get_env_mock.return_value = self.secret
        decode_mock.return_value = claims
        result: BearerClaims = validate_bearer(self.token)

        self.assertEqual(claims.get('id'), result.id)
        self.assertEqual(claims.get('expiry'), result.expiry)

        get_env_mock.assert_called_once()
        decode_mock.assert_called_once_with(
            self.token, key=self.secret, algorithms=_bearer_token_algorithms)


class TestAuthenticate(unittest.IsolatedAsyncioTestCase):
    @patch('authentication.validate_bearer')
    async def test_validation_raises_bearer_validation_exception(self, validate_bearer_mock: MagicMock) -> None:
        validate_bearer_mock.side_effect = BearerValidationException(
            'fake-token')

        expected_credentials: str = 'test-credentials'
        authorization_credentials: HTTPAuthorizationCredentials = HTTPAuthorizationCredentials(
            scheme='test-scheme', credentials=expected_credentials)

        with self.assertRaises(HTTPException) as ex:
            await authenticate(credentials=authorization_credentials)
            self.assertEqual(status.HTTP_401_UNAUTHORIZED, ex.status_code)

        validate_bearer_mock.assert_called_once_with(expected_credentials)

    @patch('authentication.validate_bearer')
    async def test_validation_raises_unexpected_exception(self, validate_bearer_mock: MagicMock) -> None:
        validate_bearer_mock.side_effect = Exception('fake exception thrown')

        expected_credentials: str = 'test-credentials'
        authorization_credentials: HTTPAuthorizationCredentials = HTTPAuthorizationCredentials(
            scheme='test-scheme', credentials=expected_credentials)

        with self.assertRaises(HTTPException) as ex:
            await authenticate(credentials=authorization_credentials)
            self.assertEqual(
                status.HTTP_500_INTERNAL_SERVER_ERROR, ex.status_code)

        validate_bearer_mock.assert_called_once_with(expected_credentials)

    @patch('authentication.validate_bearer')
    async def test_success(self, validate_bearer_mock: MagicMock) -> None:
        expected_credentials: str = 'test-credentials'
        authorization_credentials: HTTPAuthorizationCredentials = HTTPAuthorizationCredentials(
            scheme='test-scheme', credentials=expected_credentials)

        expected_bearer_claims: BearerClaims = BearerClaims(
            id=42, expiry=1750001000)
        validate_bearer_mock.return_value = expected_bearer_claims

        actual_bearer_claims: BearerClaims = await authenticate(credentials=authorization_credentials)

        self.assertEqual(expected_bearer_claims, actual_bearer_claims)
        validate_bearer_mock.assert_called_once_with(expected_credentials)
