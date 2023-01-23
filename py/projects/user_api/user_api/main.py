from logging import DEBUG, Logger
from os import getenv
from typing import Any

from acsylla import (
    Cluster,
    Result,
    Row,
    Session,
    Statement,
    create_cluster,
    create_statement,
)
from authentication.authentication import BearerClaims, authenticate
from fastapi import Depends, FastAPI, HTTPException, Response, status
from logging_utilities.utilities import get_logger
from models.user import UserCreateRequest, UserPatchRequest, UserSchema

app: FastAPI = FastAPI()
logger: Logger = get_logger(__name__, DEBUG)


current_id: int = 0


def get_id() -> int:
    """A temporary function for generating a unique ID within the context of the API's lifetime

    This method will eventually be deprecated in favour of a Snowflake ID generator.

    Returns:
        A unique ID within the context of the API's lifetime
    """
    global current_id
    current_id += 1
    return current_id


session: Session | None = None


async def cassandra_session() -> Session:
    """Retrieves an acsylla Session object, for accessing Cassandra.

    Retrieves an acsylla Session object after connecting to a cassandra cluster specified by the environment variable CASSANDRA_CLUSTER_NAME. If a Session object has already been created during the API's lifetime, it is returned without a new Session object being created.

    Returns:
        An acsylla.Session object, for accessing Cassandra.
    Raises:
        Exception: CASSANDRA_CLUSTER_NAME is not set.
    """
    global session
    if session is not None:
        return session

    cassandra_cluster_name: str | None = getenv("CASSANDRA_CLUSTER_NAME")
    if cassandra_cluster_name is None:
        raise Exception("CASSANDRA_CLUSTER_NAME is not set")

    cluster: Cluster = create_cluster(
        [cassandra_cluster_name],
        connect_timeout=30,
        request_timeout=30,
        resolve_timeout=10,
    )
    session = await cluster.create_session(keyspace="kodawari")

    return session


@app.get("/health")
async def health() -> str:
    """Retrieves the health status of the API.

    Returns:
        A string of "healthy" if the API is healthy.
    """
    return "healthy"


@app.get("/user/{id}", status_code=status.HTTP_200_OK)
async def get(id: int, session: Session = Depends(cassandra_session)) -> UserSchema:
    """Retrieves a user.

    Args:
        id: The identifier for the requested User resource.
        session: The Session required to access User data in Cassandra.
    Returns:
        A UserSchema, containing the requested User data.
    Raises:
        HTTPException: The requested User resource could not be retrieved.
    """
    statement: Statement = create_statement(
        "SELECT * FROM user WHERE id=?", parameters=1
    )
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
        logger.debug(user_schema_dict["joined"])
        return UserSchema(**user_schema_dict)


@app.post("/user", status_code=status.HTTP_201_CREATED)
async def post(
    response: Response,
    user_create_request: UserCreateRequest,
    session: Session = Depends(cassandra_session),
) -> None:
    """Creates a user.

    Patches a user and sets the Location header to the created resource path, using properties defined in the user_create_request, a generated id, and a unix timestamp.

    Args:
        response: The FastAPI response class used for setting the Location header of the created resource path.
        user_create_request: The UserSchema properties to set on the created resource.
        session: The Session required to access User data in Cassandra.
    """

    statement: Statement = create_statement(
        "INSERT INTO user (id, display_name, description, joined) VALUES (?, ?, ?, toTimestamp(now()))",
        parameters=3,
    )

    user_id: int = get_id()
    arguments: list[Any] = [
        user_id,
        user_create_request.display_name,
        user_create_request.description,
    ]
    statement.bind_list(arguments)

    await session.execute(statement)

    response.headers["Location"] = f"/user/{user_id}"


def get_patch_statement(
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
    statement: Statement
    arguments: list[Any]

    if (
        user_patch_request.display_name is not None
        and user_patch_request.description is not None
    ):
        statement = create_statement(
            "UPDATE user SET display_name=?, description=? WHERE id=? IF EXISTS",
            parameters=3,
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
        statement = create_statement(
            "UPDATE user SET display_name=? WHERE id=? IF EXISTS",
            parameters=2,
        )

        arguments = [
            user_patch_request.display_name,
            bearer_claims.id,
        ]
    elif (
        user_patch_request.display_name is None
        and user_patch_request.description is not None
    ):
        statement = create_statement(
            "UPDATE user SET description=? WHERE id=? IF EXISTS",
            parameters=2,
        )

        arguments = [
            user_patch_request.description,
            bearer_claims.id,
        ]
    else:
        return None

    statement.bind_list(arguments)

    return statement


@app.patch("/user", status_code=status.HTTP_204_NO_CONTENT)
async def patch(
    response: Response,
    user_patch_request: UserPatchRequest,
    bearer_claims: BearerClaims = Depends(authenticate),
    session: Session = Depends(cassandra_session),
) -> None:
    """Patches a user.

    Patches a user and sets the Location header to the modified resource path, using the ID retrieved from bearer_claims and properties defined in the user_patch_request.

    Args:
        response: The FastAPI response class used for setting the Location header of the modified resource path.
        user_patch_request: The User resoruce properties to update.
        bearer_claims: The claims included on the Bearer token in the request.
        session: The Session required to access User data in Cassandra.
    """
    statement: Statement | None = get_patch_statement(user_patch_request, bearer_claims)
    if statement is not None:
        await session.execute(statement)

    response.headers["Location"] = f"/user/{bearer_claims.id}"


@app.delete("/user", status_code=status.HTTP_204_NO_CONTENT)
async def delete(
    bearer_claims: BearerClaims = Depends(authenticate),
    session: Session = Depends(cassandra_session),
) -> None:
    """Deletes a user.

    Deletes a User resource using the ID retrieved from bearer_claims.

    Args:
        bearer_claims: The claims included on the Bearer token in the request.
        session: The Session required to access User data in Cassandra.
    """
    statement: Statement = create_statement(
        "DELETE FROM user WHERE id=? IF EXISTS", parameters=1
    )
    statement.bind(0, bearer_claims.id)
    await session.execute(statement)
