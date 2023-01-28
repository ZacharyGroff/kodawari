from typing import Any

from aiohttp import ClientResponse, ClientSession
from models.user import UserCreateRequest, UserPatchRequest, UserSchema
from pydantic import BaseModel, Field


class ResponseMeta(BaseModel):
    status_code: int = Field(gt=99, lt=600)
    headers: dict[Any, Any] = {}


class Client:
    def __init__(self, session: ClientSession, base_url: str):
        self.session: ClientSession = session
        self.base_url: str = base_url

    async def get_health(self) -> ResponseMeta:
        response: ClientResponse = await self.session.get(self.base_url + "/health")
        return ResponseMeta(status_code=response.status, headers=dict(response.headers))

    async def get_user(self, id: int) -> tuple[ResponseMeta, UserSchema | None]:
        response: ClientResponse = await self.session.get(self.base_url + f"/user/{id}")
        response_json: dict[Any, Any] = await response.json()

        user_schema: UserSchema | None = None
        if response.status == 200:
            user_schema = UserSchema(**response_json)
        response_meta: ResponseMeta = ResponseMeta(
            status_code=response.status, headers=dict(response.headers)
        )

        return response_meta, user_schema

    async def create_user(self, user_create_request: UserCreateRequest) -> ResponseMeta:
        response: ClientResponse = await self.session.post(
            self.base_url + "/user", json=user_create_request.dict()
        )
        return ResponseMeta(status_code=response.status, headers=dict(response.headers))

    async def patch_user(
        self, user_patch_request: UserPatchRequest, bearer_token: str
    ) -> ResponseMeta:
        request_headers: dict[str, str] = {"Authorization": f"Bearer {bearer_token}"}
        response: ClientResponse = await self.session.patch(
            self.base_url + "/user",
            json=user_patch_request.dict(),
            headers=request_headers,
        )
        return ResponseMeta(status_code=response.status, headers=dict(response.headers))

    async def delete_user(self, id: int, bearer_token: str) -> ResponseMeta:
        request_headers: dict[str, str] = {"Authorization": f"Bearer {bearer_token}"}
        response: ClientResponse = await self.session.delete(
            self.base_url + "/user", headers=request_headers
        )
        return ResponseMeta(status_code=response.status, headers=dict(response.headers))
