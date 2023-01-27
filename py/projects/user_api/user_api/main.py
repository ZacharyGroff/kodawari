from logging import DEBUG, Logger
from os import getenv
from typing import Any, Generator

from acsylla import (
    Cluster,
    PreparedStatement,
    Result,
    Row,
    Session,
    Statement,
    create_cluster,
)
from authentication.authentication import BearerClaims, authenticate
from fastapi import Depends, FastAPI, HTTPException, Response, status
from fastapi.openapi.utils import get_openapi
from identity import utilities
from logging_utilities.utilities import get_logger
from models.user import UserCreateRequest, UserPatchRequest, UserSchema

app: FastAPI = FastAPI()
logger: Logger
id_generator: Generator[int, None, None]
session: Session


def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema
    openapi_schema = get_openapi(
        title="Kodawari User API",
        version="0.1.0",
        description="Provides CRUD routes for managing UserSchema objects.",
        routes=app.routes,
    )
    app.openapi_schema = openapi_schema
    return app.openapi_schema


def get_id_generator() -> Generator[int, None, None]:
    """Retrieves an identity generator.

    Retrieves an identity generator using the instance identifier value specified by the environment variable MACHINE_INSTANCE_IDENTIFIER.

    Returns:
        An identity.utilities.id_generator.
    Raises:
        Exception: MACHINE_INSTANCE_IDENTIFIER is not set.
        Exception: MACHINE_INSTANCE_IDENTIFIER cannot be casted to an integer.
    """
    machine_instance_identifier: str | None = getenv("MACHINE_INSTANCE_IDENTIFIER")
    if machine_instance_identifier is None:
        log_message: str = "MACHINE_INSTANCE_IDENTIFIER is not set"
        logger.error(log_message)
        raise Exception(log_message)

    if not machine_instance_identifier.isdigit():
        log_message: str = "MACHINE_INSTANCE_IDENTIFIER cannot be casted to an integer"
        logger.error(log_message)
        raise Exception(log_message)

    return utilities.id_generator(int(machine_instance_identifier))


async def get_cassandra_session() -> Session:
    """Retrieves an acsylla Session object, for accessing Cassandra.

    Retrieves an acsylla Session object after connecting to a cassandra cluster specified by the environment variable CASSANDRA_CLUSTER_NAME.

    Returns:
        An acsylla.Session object, for accessing Cassandra.
    Raises:
        Exception: CASSANDRA_CLUSTER_NAME is not set.
    """
    cassandra_cluster_name: str | None = getenv("CASSANDRA_CLUSTER_NAME")
    if cassandra_cluster_name is None:
        log_message: str = "CASSANDRA_CLUSTER_NAME is not set"
        logger.error(log_message)
        raise Exception(log_message)

    cluster: Cluster = create_cluster(
        [cassandra_cluster_name],
        connect_timeout=30,
        request_timeout=30,
        resolve_timeout=10,
    )
    session = await cluster.create_session(keyspace="kodawari")

    return session


@app.on_event("startup")
async def on_startup():
    """Prepares API for requests.

    Instantiates global variables required for servicing requests, prior to the API starting.
    """
    global app, id_generator, logger, session

    app.openapi = custom_openapi
    logger = get_logger(__name__, DEBUG)
    id_generator = get_id_generator()
    session = await get_cassandra_session()


@app.get("/health", operation_id="get_health")
async def health() -> str:
    """Retrieves the health status of the API.

    Returns:
        A string of "healthy" if the API is healthy.
    """
    return "healthy"


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
    prepared: PreparedStatement = await session.create_prepared(
        "SELECT * FROM user WHERE id=?"
    )
    statement: Statement = prepared.bind()
    statement.bind(0, id)
    result: Result = await session.execute(statement)

    if result.count() == 0:
        raise HTTPException(status_code=404, detail="User not found")
    elif result.count() > 1:
        logger.error(f"Multiple results returned when querying for user with id: {id}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)
    else:
        user_schema_row: Row | None = result.first()
        if user_schema_row is None:
            raise HTTPException(status_code=404, detail="User not found")

        user_schema_dict: dict[Any, Any] = user_schema_row.as_dict()
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

    prepared: PreparedStatement = await session.create_prepared(
        "INSERT INTO user (id, display_name, description) VALUES (?, ?, ?)"
    )
    statement: Statement = prepared.bind()

    user_id: int = next(id_generator)
    arguments: list[Any] = [
        user_id,
        user_create_request.display_name,
        user_create_request.description,
    ]
    statement.bind_list(arguments)

    await session.execute(statement)

    response.headers["Location"] = f"/user/{user_id}"


async def get_patch_statement(
    user_patch_request: UserPatchRequest, bearer_claims: BearerClaims
) -> Statement | None:
    """Retrieves a Statement for patching.

    Retrieves a Statement for patching a User resource in Cassandra.

    Args:
        user_patch_request: The User resource properties to update.
        bearer_claims: The claims included on the Bearer token in the request.
    Returns:
        An optional Statement for patching a User resource. None if no data requires patching.
    """
    prepared: PreparedStatement
    arguments: list[Any]

    if (
        user_patch_request.display_name is not None
        and user_patch_request.description is not None
    ):
        prepared: PreparedStatement = await session.create_prepared(
            "UPDATE user SET display_name=?, description=? WHERE id=? IF EXISTS",
        )

        arguments = [
            user_patch_request.display_name,
            user_patch_request.description,
            bearer_claims.id,
        ]
    elif (
        user_patch_request.display_name is not None
        and user_patch_request.description is None
    ):
        prepared: PreparedStatement = await session.create_prepared(
            "UPDATE user SET display_name=? WHERE id=? IF EXISTS",
        )

        arguments = [
            user_patch_request.display_name,
            bearer_claims.id,
        ]
    elif (
        user_patch_request.display_name is None
        and user_patch_request.description is not None
    ):
        prepared: PreparedStatement = await session.create_prepared(
            "UPDATE user SET description=? WHERE id=? IF EXISTS",
        )

        arguments = [
            user_patch_request.description,
            bearer_claims.id,
        ]
    else:
        return None

    statement: Statement = prepared.bind()
    statement.bind_list(arguments)

    return statement


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
    statement: Statement | None = await get_patch_statement(
        user_patch_request, bearer_claims
    )
    if statement is not None:
        await session.execute(statement)

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
    prepared: PreparedStatement = await session.create_prepared(
        "DELETE FROM user WHERE id=? IF EXISTS"
    )
    statement: Statement = prepared.bind()
    statement.bind(0, bearer_claims.id)
    await session.execute(statement)
