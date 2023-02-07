from logging import DEBUG, Logger
from typing import Any, Generator

from acsylla import Session
from authentication.authentication import BearerClaims, authenticate
from database.cassandra import (
    create_resource,
    delete_resource_by_id,
    get_cassandra_session,
    get_resource_by_id,
    patch_resource,
)
from fastapi import Depends, FastAPI, HTTPException, Response, status
from identity import utilities
from logging_utilities.utilities import get_logger
from models.user import UserCreateRequest, UserPatchRequest, UserSchema
from rest_api_utilities.fastapi import get_custom_openapi_wrapper, health_router

app: FastAPI = FastAPI()
app.include_router(health_router)
logger: Logger
id_generator: Generator[int, None, None]
session: Session
user_table_name: str = "user"


@app.on_event("startup")
async def on_startup():
    """Prepares API for requests.

    Instantiates global variables required for servicing requests, prior to the API starting.
    """
    global app, id_generator, logger, session

    logger = get_logger(__name__, DEBUG)
    try:
        app.openapi = get_custom_openapi_wrapper(
            app,
            title="Kodawari User API",
            version="0.1.0",
            description="Provides CRUD routes for managing UserSchema objects.",
        )
        id_generator = utilities.get_id_generator()
        session = await get_cassandra_session("kodawari")
    except Exception as ex:
        logger.error("An unexpected error has occurred during startup.")
        raise ex


@app.get("/user/{id}", status_code=status.HTTP_200_OK, operation_id="get_user")
async def get(id: int) -> UserSchema:
    """Retrieves a user.

    Args:
        id: The identifier for the requested User resource.
    Returns:
        A UserSchema, containing the requested User data.
    Raises:
        HTTPException: The requested User resource could not be retrieved.
    """
    user_schema_dict: dict[str, Any] | None = await get_resource_by_id(
        session, user_table_name, id
    )
    if user_schema_dict is None:
        raise HTTPException(status_code=404, detail="User not found")

    joined: int = utilities.get_timestamp(user_schema_dict["id"])
    user_schema_dict["joined"] = joined
    return UserSchema(**user_schema_dict)


@app.post("/user", status_code=status.HTTP_201_CREATED, operation_id="create_user")
async def post(response: Response, user_create_request: UserCreateRequest) -> None:
    """Creates a user.

    Patches a user and sets the Location header to the created resource path, using properties defined in the user_create_request, a generated id, and a unix timestamp.

    Args:
        response: The FastAPI response class used for setting the Location header of the created resource path.
        user_create_request: The UserSchema properties to set on the created resource.
    """

    column_names: list[str] = ["id", "display_name", "description"]

    user_id: int = next(id_generator)
    values: list[Any] = [
        user_id,
        user_create_request.display_name,
        user_create_request.description,
    ]

    await create_resource(session, user_table_name, column_names, values)

    response.headers["Location"] = f"/user/{user_id}"


@app.patch("/user", status_code=status.HTTP_204_NO_CONTENT, operation_id="patch_user")
async def patch(
    response: Response,
    user_patch_request: UserPatchRequest,
    bearer_claims: BearerClaims = Depends(authenticate),
) -> None:
    """Patches a user.

    Patches a user and sets the Location header to the modified resource path, using the ID retrieved from bearer_claims and properties defined in the user_patch_request.

    Args:
        response: The FastAPI response class used for setting the Location header of the modified resource path.
        user_patch_request: The User resoruce properties to update.
        bearer_claims: The claims included on the Bearer token in the request.
    """
    await patch_resource(
        session, user_table_name, user_patch_request.dict(), bearer_claims.id
    )
    response.headers["Location"] = f"/user/{bearer_claims.id}"


@app.delete("/user", status_code=status.HTTP_204_NO_CONTENT, operation_id="delete_user")
async def delete(
    bearer_claims: BearerClaims = Depends(authenticate),
) -> None:
    """Deletes a user.

    Deletes a User resource using the ID retrieved from bearer_claims.

    Args:
        bearer_claims: The claims included on the Bearer token in the request.
    """
    await delete_resource_by_id(session, user_table_name, bearer_claims.id)
