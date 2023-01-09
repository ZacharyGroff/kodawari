from datetime import datetime
from fastapi import HTTPException, Depends, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jwt import decode
from pydantic import BaseModel
from os import getenv
from typing import Any, Dict

_secret_environment_variable = 'KODAWARI_SECRET_KEY'
_bearer_token_algorithms = ['HS256']
_security_scheme = HTTPBearer()


class BearerValidationException(Exception):
    def __init__(self, token: str) -> None:
        super().__init__(f'Failed to validate token: ${token}')


class SecretEnvironmentVariableException(Exception):
    def __init__(self) -> None:
        super().__init__(f'Failed to retrieve {_secret_environment_variable}')


class BearerClaims(BaseModel):
    id: int
    expiry: int


def validate_bearer(token: str) -> BearerClaims:
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
    token = credentials.credentials
    try:
        bearer_claims: BearerClaims = validate_bearer(token)
        return bearer_claims
    except BearerValidationException:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED)
    except:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)
