from datetime import datetime
from fastapi import HTTPException, Depends, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jwt import InvalidSignatureError, decode
from pydantic import BaseModel
from os import getenv
from typing import Any, Dict

_secret_environment_variable = 'KODAWARI_SECRET_KEY'
_bearer_token_algorithms = ['HS256']
_security_scheme = HTTPBearer()


class BearerValidationException(Exception):
    """The access token from a request has failed validation."""

    def __init__(self, token: str) -> None:
        super().__init__(f'Failed to validate token: ${token}')


class SecretEnvironmentVariableException(Exception):
    """The secret environment variable is not set."""

    def __init__(self) -> None:
        super().__init__(f'Failed to retrieve {_secret_environment_variable}')


class BearerClaims(BaseModel):
    """ A dataclass containing properties from an access token.

    Attributes:
        id: The id of the user issuing a request.
        expiry: The expiration date of the request access token, expressed as a Unix timestamp in seconds.
    """
    id: int
    expiry: int


def validate_bearer(token: str) -> BearerClaims:
    """Validates bearer tokens

    Validates bearer tokens by decrypting the encrypted token and validating the token is not expired.

    Args:
        token: An encrypted token.

    Returns:
        A BearerClaims object containing claims from the encrypted token.

    Raises:
        SecretEnvironmentVariableException: The secret environment variable was unable to be retrieved.
        BearerValidationException: The token was expired.
    """
    secret: str | None = getenv(_secret_environment_variable)
    if secret is None:
        raise SecretEnvironmentVariableException

    decoded_json: Dict[str, Any] = decode(
        token, key=secret, algorithms=_bearer_token_algorithms)
    bearer_claims: BearerClaims = BearerClaims(**decoded_json)

    ms_since_epoch: int = int(datetime.now().timestamp())
    if bearer_claims.expiry < ms_since_epoch:
        raise BearerValidationException(token)

    return bearer_claims


async def authenticate(credentials: HTTPAuthorizationCredentials = Depends(_security_scheme)) -> BearerClaims:
    """Authenticates user credentials.

    Authenticates user credentials by decrypting the JWT included on the HTTPAuthorizationCredentials and validating the expiry.

    Args:
        credentials: The HTTPAuthorizationCredentials provided in a request, containing a Bearer Token property (credentials).

    Returns:
        A BearerClaims object containing claims from the Bearer Token.

    Raises:
        HTTPException: The user was unauthorized or an internal server error occurred while processing the request.
    """

    token = credentials.credentials
    try:
        bearer_claims: BearerClaims = validate_bearer(token)
        return bearer_claims
    except (BearerValidationException, InvalidSignatureError):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED)
    except:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)
