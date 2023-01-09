from datetime import datetime
from jwt import decode
from pydantic import BaseModel
from os import getenv
from typing import Any, Dict

_secret_environment_variable = 'KODAWARI_SECRET_KEY'
_bearer_token_algorithms = ['HS256']


class BearerValidationException(Exception):
    def __init__(self, token: str) -> None:
        super().__init__(f'Failed to validate token: ${token}')


class BearerClaims(BaseModel):
    id: int
    expiry: int


def validate_bearer(token: str) -> BearerClaims:
    secret: str | None = getenv(_secret_environment_variable)
    if secret is None:
        raise BearerValidationException(token)
    try:
        decoded_json: Dict[str, Any] = decode(
            token, key=secret, algorithms=_bearer_token_algorithms)
        bearer_claims: BearerClaims = BearerClaims(**decoded_json)

        ms_since_epoch: int = int(datetime.now().timestamp())
        if bearer_claims.expiry < ms_since_epoch:
            raise BearerValidationException(token)

        return bearer_claims
    except Exception:
        raise BearerValidationException(token)
