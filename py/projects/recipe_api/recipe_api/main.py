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
from models.recipe import (
    RecipeCreateRequest,
    RecipePatchRequest,
    RecipeSchema,
    VariationCreateRequest,
    VariationPatchRequest,
    VariationSchema,
)

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
    table_name: str, to_patch: dict[str, Any], id: int
) -> Statement | None:
    """Retrieves a Statement for patching.

    Retrieves a Statement for patching a resource in Cassandra.

    Args:
        table_name: The name of the table to run the patch statement.
        to_patch: A dictionary key-value pairs to include in the UPDATE statement.
        id: The id of the resource being patched.

    Returns:
        An optional Statement for patching a resource. None if no data requires patching.
    """
    eligible_fields: list[str] = []
    eligible_values: list[Any] = []
    for key, value in to_patch.items():
        if value is not None:
            eligible_fields.append(key)
            eligible_values.append(value)

    if len(eligible_fields) < 1:
        return None

    fields: str = "=?, ".join(eligible_fields) + "=?"
    prepared: PreparedStatement = await session.create_prepared(
        f"UPDATE {table_name} SET {fields} WHERE id=? IF EXISTS",
    )
    statement: Statement = prepared.bind()
    statement.bind_list(eligible_values + [id])

    return statement


@app.patch(
    "/recipe/{id}", status_code=status.HTTP_204_NO_CONTENT, operation_id="patch_recipe"
)
async def patch_recipe(
    id: int,
    response: Response,
    recipe_patch_request: RecipePatchRequest,
    bearer_claims: BearerClaims = Depends(authenticate),
) -> None:
    """Patches a Recipe.

    Patches a Recipe and sets the Location header to the modified resource path, using the ID retrieved from bearer_claims and properties defined in the recipe_patch_request.

    Args:
        id: The requested variation to patch.
        response: The FastAPI response class used for setting the Location header of the modified resource path.
        recipe_patch_request: The Recipe resource properties to update.
        bearer_claims: The claims included on the Bearer token in the request.
    Raises:
        HTTPException: The request is not authorized.
    """
    requested_recipe: RecipeSchema = await get_recipe(id)
    if requested_recipe.author_id != bearer_claims.id:
        logger.error(
            f"Unauthorized deletion attempt of recipe: {requested_recipe.id} from user: {bearer_claims.id}"
        )
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN)

    statement: Statement | None = await get_patch_statement(
        "recipe", recipe_patch_request.dict(), id
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
    Raises:
        HTTPException: The request is not authorized.
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


@app.get(
    "/variation/{id}", status_code=status.HTTP_200_OK, operation_id="get_variation"
)
async def get_variation(id: int) -> VariationSchema:
    """Retrieves a variation.

    Args:
        id: The identifier for the requested Variation resource.
    Returns:
        A VariationSchema, containing the requested Variation data.
    Raises:
        HTTPException: The requested Variation resource could not be retrieved.
    """
    prepared: PreparedStatement = await session.create_prepared(
        "SELECT * FROM variation WHERE id=?"
    )
    statement: Statement = prepared.bind()
    statement.bind(0, id)
    result: Result = await session.execute(statement)

    if result.count() == 0:
        raise HTTPException(status_code=404, detail="Variation not found")
    elif result.count() > 1:
        logger.error(
            f"Multiple results returned when querying for Variation with id: {id}"
        )
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR)
    else:
        variation_schema_row: Row | None = result.first()
        if variation_schema_row is None:
            raise HTTPException(status_code=404, detail="Variation not found")

        variation_schema_dict: dict[Any, Any] = variation_schema_row.as_dict()
        created_at: int = utilities.get_timestamp(variation_schema_dict["id"])
        variation_schema_dict["created_at"] = created_at
        return VariationSchema(**variation_schema_dict)


@app.post(
    "/variation", status_code=status.HTTP_201_CREATED, operation_id="create_variation"
)
async def post_variation(
    response: Response,
    variation_create_request: VariationCreateRequest,
    bearer_claims: BearerClaims = Depends(authenticate),
) -> None:
    """Creates a Variation.

    Creates a Variation and sets the Location header to the created resource path, using properties defined in the variation_create_request, a generated id, and a unix timestamp.

    Args:
        response: The FastAPI response class used for setting the Location header of the created resource path.
        variation_create_request: The VariationSchema properties to set on the created resource.
    Raises:
        HTTPException: A recipe with the recipe_id in the request was not found.
    """
    requested_recipe: RecipeSchema = await get_recipe(
        variation_create_request.recipe_id
    )
    if requested_recipe is None:
        raise HTTPException(
            status_code=404,
            detail="A recipe with the recipe_id in the request was not found.",
        )

    prepared: PreparedStatement = await session.create_prepared(
        "INSERT INTO variation (id, author_id, recipe_id, name, ingredients, process, notes, views, vote_diff) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)"
    )
    statement: Statement = prepared.bind()

    variation_id: int = next(id_generator)
    arguments: list[Any] = [
        variation_id,
        bearer_claims.id,
        variation_create_request.recipe_id,
        variation_create_request.name,
        variation_create_request.ingredients,
        variation_create_request.process,
        variation_create_request.notes,
        0,
        0,
    ]
    statement.bind_list(arguments)

    await session.execute(statement)

    response.headers["Location"] = f"/variation/{variation_id}"


@app.patch(
    "/variation/{id}",
    status_code=status.HTTP_204_NO_CONTENT,
    operation_id="patch_variation",
)
async def patch_variation(
    id: int,
    response: Response,
    variation_patch_request: VariationPatchRequest,
    bearer_claims: BearerClaims = Depends(authenticate),
) -> None:
    """Patches a Variation.

    Patches a Variation and sets the Location header to the modified resource path, using the ID retrieved from bearer_claims and properties defined in the variation_patch_request.

    Args:
        id: The requested variation to patch.
        response: The FastAPI response class used for setting the Location header of the modified resource path.
        variation_patch_request: The variation resource properties to update.
        bearer_claims: The claims included on the Bearer token in the request.
    Raises:
        HTTPException: The request is not authorized.
    """
    requested_variation: VariationSchema = await get_variation(id)
    if requested_variation.author_id != bearer_claims.id:
        logger.error(
            f"Unauthorized deletion attempt of variation: {requested_variation.id} from user: {bearer_claims.id}"
        )
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN)

    statement: Statement | None = await get_patch_statement(
        "variation", variation_patch_request.dict(), id
    )
    if statement is not None:
        await session.execute(statement)

    response.headers["Location"] = f"/variation/{requested_variation.id}"


@app.delete(
    "/variation/{id}",
    status_code=status.HTTP_204_NO_CONTENT,
    operation_id="delete_variation",
)
async def delete_variation(
    id: int,
    bearer_claims: BearerClaims = Depends(authenticate),
) -> None:
    """Deletes a Variation.

    Deletes a Variation resource using the provided id after verifying ownership with the id from bearer_claims.

    Args:
        id: The identifier for the variation to delete.
        bearer_claims: The claims included on the Bearer token in the request.
    Raises:
        HTTPException: The request is not authorized.
    """
    requested_variation: VariationSchema = await get_variation(id)
    if requested_variation.author_id != bearer_claims.id:
        logger.error(
            f"Unauthorized deletion attempt of variation: {requested_variation.id} from user: {bearer_claims.id}"
        )
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN)

    prepared: PreparedStatement = await session.create_prepared(
        "DELETE FROM variation WHERE id=? IF EXISTS"
    )
    statement: Statement = prepared.bind()
    statement.bind(0, id)
    await session.execute(statement)
