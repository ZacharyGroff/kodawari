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
from models.recipe import RecipeCreateRequest, RecipePatchRequest, RecipeSchema

app: FastAPI = FastAPI()
logger: Logger
id_generator: Generator[int, None, None]
session: Session


def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema
    openapi_schema = get_openapi(
        title="Kodawari Recipe API",
        version="0.1.0",
        description="Provides CRUD routes for managing RecipeSchema and VariationSchema objects.",
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


@app.get("/recipe/{id}", status_code=status.HTTP_200_OK, operation_id="get_recipe")
async def get_recipe(id: int) -> RecipeSchema:
    """Retrieves a recipe.

    Args:
        id: The identifier for the requested Recipe resource.
    Returns:
        A RecipeSchema, containing the requested Recipe data.
    Raises:
        HTTPException: The requested Recipe resource could not be retrieved.
    """
    prepared: PreparedStatement = await session.create_prepared(
        "SELECT * FROM recipe WHERE id=?"
    )
    statement: Statement = prepared.bind()
    statement.bind(0, id)
    result: Result = await session.execute(statement)

    if result.count() == 0:
        raise HTTPException(status_code=404, detail="Recipe not found")
    elif result.count() > 1:
        logger.error(
            f"Multiple results returned when querying for recipe with id: {id}"
        )
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)
    else:
        recipe_schema_row: Row | None = result.first()
        if recipe_schema_row is None:
            raise HTTPException(status_code=404, detail="Recipe not found")

        recipe_schema_dict: dict[Any, Any] = recipe_schema_row.as_dict()
        created_at: int = utilities.get_timestamp(recipe_schema_dict["id"])
        recipe_schema_dict["created_at"] = created_at
        return RecipeSchema(**recipe_schema_dict)


@app.post("/recipe", status_code=status.HTTP_201_CREATED, operation_id="create_recipe")
async def post_recipe(
    response: Response,
    recipe_create_request: RecipeCreateRequest,
    bearer_claims: BearerClaims = Depends(authenticate),
) -> None:
    """Creates a Recipe.

    Creates a recipe and sets the Location header to the created resource path, using properties defined in the recipe_create_request, a generated id, and a unix timestamp.

    Args:
        response: The FastAPI response class used for setting the Location header of the created resource path.
        recipe_create_request: The RecipeSchema properties to set on the created resource.
    """

    prepared: PreparedStatement = await session.create_prepared(
        "INSERT INTO recipe (id, author_id, name, description, views, subscribers, vote_diff) VALUES (?, ?, ?, ?, ?, ?, ?)"
    )
    statement: Statement = prepared.bind()

    recipe_id: int = next(id_generator)
    arguments: list[Any] = [
        recipe_id,
        bearer_claims.id,
        recipe_create_request.name,
        recipe_create_request.description,
        0,
        0,
        0,
    ]
    statement.bind_list(arguments)

    await session.execute(statement)

    response.headers["Location"] = f"/recipe/{recipe_id}"


async def get_patch_statement(
    recipe_patch_request: RecipePatchRequest, bearer_claims: BearerClaims
) -> Statement | None:
    """Retrieves a Statement for patching.

    Retrieves a Statement for patching a Recipe resource in Cassandra.

    Args:
        recipe_patch_request: The Recipe resource properties to update.
    Returns:
        An optional Statement for patching a Recipe resource. None if no data requires patching.
    """
    prepared: PreparedStatement
    arguments: list[Any]

    if (
        recipe_patch_request.name is not None
        and recipe_patch_request.description is not None
    ):
        prepared: PreparedStatement = await session.create_prepared(
            "UPDATE recipe SET name=?, description=? WHERE id=? IF EXISTS",
        )

        arguments = [
            recipe_patch_request.name,
            recipe_patch_request.description,
            recipe_patch_request.id,
        ]
    elif (
        recipe_patch_request.name is not None
        and recipe_patch_request.description is None
    ):
        prepared: PreparedStatement = await session.create_prepared(
            "UPDATE recipe SET name=? WHERE id=? IF EXISTS",
        )

        arguments = [
            recipe_patch_request.name,
            recipe_patch_request.id,
        ]
    elif (
        recipe_patch_request.name is None
        and recipe_patch_request.description is not None
    ):
        prepared: PreparedStatement = await session.create_prepared(
            "UPDATE recipe SET description=? WHERE id=? IF EXISTS",
        )

        arguments = [
            recipe_patch_request.description,
            recipe_patch_request.id,
        ]
    else:
        return None

    statement: Statement = prepared.bind()
    statement.bind_list(arguments)

    return statement


@app.patch(
    "/recipe", status_code=status.HTTP_204_NO_CONTENT, operation_id="patch_recipe"
)
async def patch_recipe(
    response: Response,
    recipe_patch_request: RecipePatchRequest,
    bearer_claims: BearerClaims = Depends(authenticate),
) -> None:
    """Patches a Recipe.

    Patches a Recipe and sets the Location header to the modified resource path, using the ID retrieved from bearer_claims and properties defined in the recipe_patch_request.

    Args:
        response: The FastAPI response class used for setting the Location header of the modified resource path.
        recipe_patch_request: The Recipe resource properties to update.
        bearer_claims: The claims included on the Bearer token in the request.
    """
    requested_recipe: RecipeSchema = await get_recipe(recipe_patch_request.id)
    if requested_recipe.author_id != bearer_claims.id:
        logger.error(
            f"Unauthorized deletion attempt of recipe: {requested_recipe.id} from user: {bearer_claims.id}"
        )
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN)

    statement: Statement | None = await get_patch_statement(
        recipe_patch_request, bearer_claims
    )
    if statement is not None:
        await session.execute(statement)

    response.headers["Location"] = f"/recipe/{requested_recipe.id}"


@app.delete(
    "/recipe/{id}", status_code=status.HTTP_204_NO_CONTENT, operation_id="delete_recipe"
)
async def delete_recipe(
    id: int,
    bearer_claims: BearerClaims = Depends(authenticate),
) -> None:
    """Deletes a recipe.

    Deletes a Recipe resource using the provided id after verifying ownership with the id from bearer_claims.

    Args:
        id: The identifier for the recipe to delete.
        bearer_claims: The claims included on the Bearer token in the request.
    """
    requested_recipe: RecipeSchema = await get_recipe(id)
    if requested_recipe.author_id != bearer_claims.id:
        logger.error(
            f"Unauthorized deletion attempt of recipe: {requested_recipe.id} from user: {bearer_claims.id}"
        )
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN)

    prepared: PreparedStatement = await session.create_prepared(
        "DELETE FROM recipe WHERE id=? IF EXISTS"
    )
    statement: Statement = prepared.bind()
    statement.bind(0, id)
    await session.execute(statement)
