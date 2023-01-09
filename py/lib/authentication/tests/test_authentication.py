from authentication import BearerClaims, BearerValidationException, validate_bearer, _bearer_token_algorithms
from typing import Any, Dict
import unittest
from unittest.mock import MagicMock, patch


class TestValidateBearer(unittest.TestCase):
    token: str = 'test'
    secret: str = 'test_secret'

    @patch('authentication.getenv')
    def test_secret_is_none(self, get_env_mock: MagicMock) -> None:
        get_env_mock.return_value = None
        with self.assertRaises(BearerValidationException):
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
        with self.assertRaises(BearerValidationException):
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
