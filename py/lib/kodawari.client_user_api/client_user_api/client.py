from typing import Any

from aiohttp import ClientResponse, ClientSession
from models.user import UserCreateRequest, UserPatchRequest, UserSchema
from pydantic import BaseModel, Field


class ResponseMeta(BaseModel):
    """Meta data for a server's response.

    Attributes:
        status_code: An integer representing the status code from the server's response.
        headers: A dictionary of HTTP headers from the server's response.
    """

    status_code: int = Field(gt=99, lt=600)
    headers: dict[Any, Any] = {}


class Client:
    """A client for kodawari.user_api.

    Attributes:
        session: An aiohttp.ClientSession used for requests.
        base_url: The base url for kodawari.user_api.
    """

    def __init__(self, session: ClientSession, base_url: str):
        self.session: ClientSession = session
        self.base_url: str = base_url

    async def get_health(self) -> ResponseMeta:
        """Retrieves health status of kodawari.user_api.

        Args:
            self: A Client instance.

        Returns: Response meta data in the form of ResponseMeta.
        """
        response: ClientResponse = await self.session.get(self.base_url + "/health")
        return ResponseMeta(status_code=response.status, headers=dict(response.headers))

    async def get_user(self, id: int) -> tuple[ResponseMeta, UserSchema | None]:
        """Retrieves a user.

        Args:
            self: A Client instance.
            id: The identifier for a user.

        Returns: A tuple of response meta data in the form of ResponseMeta and a noneable UserSchema.
        """
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
        """Creates a user.

        Args:
            self: A Client instance.
            user_create_request: The request parameters for the create route.

        Returns: Response meta data in the form of ResponseMeta.
        """
        response: ClientResponse = await self.session.post(
            self.base_url + "/user", json=user_create_request.dict()
        )
        return ResponseMeta(status_code=response.status, headers=dict(response.headers))

    async def patch_user(
        self, user_patch_request: UserPatchRequest, bearer_token: str
    ) -> ResponseMeta:
        """Patches a user.

        Args:
            self: A Client instance.
            user_patch_request: The request parameters for the patch route.
            bearer_token: A Bearer Token string.

        Returns: Response meta data in the form of ResponseMeta.
        """
        request_headers: dict[str, str] = {"Authorization": f"Bearer {bearer_token}"}
        response: ClientResponse = await self.session.patch(
            self.base_url + "/user",
            json=user_patch_request.dict(),
            headers=request_headers,
        )
        return ResponseMeta(status_code=response.status, headers=dict(response.headers))

    async def delete_user(self, id: int, bearer_token: str) -> ResponseMeta:
        """Deletes a user.

        Args:
            self: A Client instance.
            id: The identifier for a user.
            bearer_token: A Bearer Token string.

        Returns: Response meta data in the form of ResponseMeta.
        """
        request_headers: dict[str, str] = {"Authorization": f"Bearer {bearer_token}"}
        response: ClientResponse = await self.session.delete(
            self.base_url + "/user", headers=request_headers
        )
        return ResponseMeta(status_code=response.status, headers=dict(response.headers))
