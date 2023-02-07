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
from event_streaming.models import RecipeEvent, RecipeEventEncoder, RecipeEventType
from event_streaming.utilities import EventProducer, get_event_producer
from fastapi import Depends, FastAPI, HTTPException, Response, status
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
from rest_api_utilities.fastapi import get_custom_openapi_wrapper, health_router

app: FastAPI = FastAPI()
app.include_router(health_router)
logger: Logger
id_generator: Generator[int, None, None]
producer: EventProducer
session: Session
__recipe_table_name: str = "recipe"
__variation_table_name: str = "variation"


@app.on_event("startup")
async def on_startup():
    """Prepares API for requests.

    Instantiates global variables required for servicing requests, prior to the API starting.
    """
    global app, id_generator, logger, producer, session

    logger = get_logger(__name__, DEBUG)
    try:
        app.openapi = get_custom_openapi_wrapper(
            app,
            title="Kodawari Recipe API",
            version="0.1.0",
            description="Provides CRUD routes for managing RecipeSchema and VariationSchema objects.",
        )
        id_generator = utilities.get_id_generator()
        producer = get_event_producer(
            RecipeEventEncoder, error_cb=lambda x: logger.warn(x)
        )
        session = await get_cassandra_session("kodawari")
    except Exception as ex:
        logger.error("An unexpected error has occurred during startup.")
        raise ex


@app.get("/recipe/{id}", status_code=status.HTTP_200_OK, operation_id="get_recipe")
async def get_recipe(
    id: int, bearer_claims: BearerClaims = Depends(authenticate)
) -> RecipeSchema:
    """Retrieves a recipe.

    Args:
        id: The identifier for the requested Recipe resource.
    Returns:
        A RecipeSchema, containing the requested Recipe data.
    Raises:
        HTTPException: The requested Recipe resource could not be retrieved.
    """
    recipe_schema_dict: dict[str, Any] | None = await get_resource_by_id(
        session, __recipe_table_name, id
    )
    if recipe_schema_dict is None:
        raise HTTPException(status_code=404, detail="Recipe not found")

    created_at: int = utilities.get_timestamp(recipe_schema_dict["id"])
    recipe_schema_dict["created_at"] = created_at
    recipe_schema: RecipeSchema = RecipeSchema(**recipe_schema_dict)

    recipe_viewed_event: RecipeEvent = RecipeEvent(
        event_type=RecipeEventType.VIEWED,
        actor_id=bearer_claims.id,
        recipe_id=recipe_schema.id,
    )
    producer.produce(
        "recipe.viewed",
        key=str(recipe_viewed_event.recipe_id),
        value=recipe_viewed_event,
    )

    return recipe_schema


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

    recipe_id: int = next(id_generator)
    column_names: list[str] = ["id", "author_id", "name", "description"]
    values: list[Any] = [
        recipe_id,
        bearer_claims.id,
        recipe_create_request.name,
        recipe_create_request.description,
    ]
    await create_resource(session, __recipe_table_name, column_names, values)

    response.headers["Location"] = f"/recipe/{recipe_id}"

    recipe_created_event: RecipeEvent = RecipeEvent(
        event_type=RecipeEventType.CREATED,
        actor_id=bearer_claims.id,
        recipe_id=recipe_id,
    )
    producer.produce(
        "recipe.created",
        key=str(recipe_created_event.recipe_id),
        value=recipe_created_event,
    )


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
    requested_recipe_dict: dict[str, Any] | None = await get_resource_by_id(
        session, __recipe_table_name, id
    )
    if requested_recipe_dict is None:
        raise HTTPException(status_code=404, detail="Recipe not found")

    if requested_recipe_dict["author_id"] != bearer_claims.id:
        logger.error(
            f"Unauthorized deletion attempt of recipe: {requested_recipe_dict['id']} from user: {bearer_claims.id}"
        )
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN)

    await patch_resource(session, __recipe_table_name, recipe_patch_request.dict(), id)
    response.headers["Location"] = f"/recipe/{id}"

    recipe_modified_event: RecipeEvent = RecipeEvent(
        event_type=RecipeEventType.MODIFIED,
        actor_id=bearer_claims.id,
        recipe_id=id,
    )
    producer.produce(
        "recipe.modified",
        key=str(id),
        value=recipe_modified_event,
    )


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
    requested_recipe_dict: dict[str, Any] | None = await get_resource_by_id(
        session, __recipe_table_name, id
    )
    if requested_recipe_dict is None:
        raise HTTPException(status_code=404, detail="Recipe not found")

    if requested_recipe_dict["author_id"] != bearer_claims.id:
        logger.error(
            f"Unauthorized deletion attempt of recipe: {id} from user: {bearer_claims.id}"
        )
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN)

    await delete_resource_by_id(session, __recipe_table_name, id)

    recipe_deleted_event: RecipeEvent = RecipeEvent(
        event_type=RecipeEventType.DELETED,
        actor_id=bearer_claims.id,
        recipe_id=id,
    )
    producer.produce(
        "recipe.deleted",
        key=str(id),
        value=recipe_deleted_event,
    )


@app.get(
    "/variation/{id}", status_code=status.HTTP_200_OK, operation_id="get_variation"
)
async def get_variation(
    id: int, bearer_claims: BearerClaims = Depends(authenticate)
) -> VariationSchema:
    """Retrieves a variation.

    Args:
        id: The identifier for the requested Variation resource.
    Returns:
        A VariationSchema, containing the requested Variation data.
    Raises:
        HTTPException: The requested Variation resource could not be retrieved.
    """

    variation_schema_dict: dict[str, Any] | None = await get_resource_by_id(
        session, __variation_table_name, id
    )
    if variation_schema_dict is None:
        raise HTTPException(status_code=404, detail="Variation not found")

    created_at: int = utilities.get_timestamp(variation_schema_dict["id"])
    variation_schema_dict["created_at"] = created_at
    variation_viewed_event: RecipeEvent = RecipeEvent(
        event_type=RecipeEventType.VIEWED,
        actor_id=bearer_claims.id,
        recipe_id=id,
    )
    producer.produce(
        "variation.viewed",
        key=str(id),
        value=variation_viewed_event,
    )

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
    requested_recipe_dict: dict[str, Any] | None = await get_resource_by_id(
        session, __recipe_table_name, variation_create_request.recipe_id
    )
    if requested_recipe_dict is None:
        raise HTTPException(
            status_code=404,
            detail="A recipe with the provided recipe_id was not found.",
        )

    variation_id: int = next(id_generator)
    column_names: list[str] = [
        "id",
        "author_id",
        "recipe_id",
        "name",
        "ingredients",
        "process",
        "notes",
    ]
    values: list[Any] = [
        variation_id,
        bearer_claims.id,
        variation_create_request.recipe_id,
        variation_create_request.name,
        variation_create_request.ingredients,
        variation_create_request.process,
        variation_create_request.notes,
    ]

    await create_resource(session, __variation_table_name, column_names, values)

    response.headers["Location"] = f"/variation/{variation_id}"

    variation_created_event: RecipeEvent = RecipeEvent(
        event_type=RecipeEventType.CREATED,
        actor_id=bearer_claims.id,
        recipe_id=variation_id,
    )
    producer.produce(
        "variation.created",
        key=str(variation_id),
        value=variation_created_event,
    )


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
    requested_variation_dict: dict[str, Any] | None = await get_resource_by_id(
        session, __variation_table_name, id
    )
    if requested_variation_dict is None:
        raise HTTPException(
            status_code=404,
            detail="A variation with the provided id was not found.",
        )

    if requested_variation_dict["author_id"] != bearer_claims.id:
        logger.error(
            f"Unauthorized deletion attempt of variation: {id} from user: {bearer_claims.id}"
        )
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN)

    await patch_resource(
        session, __variation_table_name, variation_patch_request.dict(), id
    )

    response.headers["Location"] = f"/variation/{id}"

    variation_modified_event: RecipeEvent = RecipeEvent(
        event_type=RecipeEventType.MODIFIED,
        actor_id=bearer_claims.id,
        recipe_id=id,
    )
    producer.produce(
        "variation.modified",
        key=str(id),
        value=variation_modified_event,
    )


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
    requested_variation_dict: dict[str, Any] | None = await get_resource_by_id(
        session, __variation_table_name, id
    )
    if requested_variation_dict is None:
        raise HTTPException(
            status_code=404,
            detail="A variation with the provided id was not found.",
        )

    if requested_variation_dict["author_id"] != bearer_claims.id:
        logger.error(
            f"Unauthorized deletion attempt of variation: {id} from user: {bearer_claims.id}"
        )
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN)

    await delete_resource_by_id(session, __variation_table_name, id)

    variation_deleted_event: RecipeEvent = RecipeEvent(
        event_type=RecipeEventType.DELETED,
        actor_id=bearer_claims.id,
        recipe_id=id,
    )
    producer.produce(
        "variation.deleted",
        key=str(id),
        value=variation_deleted_event,
    )
