from fastapi import APIRouter, FastAPI
from fastapi.openapi.utils import get_openapi


def get_custom_openapi_wrapper(
    app: FastAPI, title: str, version: str, description: str
):
    """A wrapper for a function that retrieves openapi_schema on the provided FastAPI instance.

    Args:
        app: The FastAPI instance, on which openapi_schema is stored.
        title: The title of the api on the openapi_schema.
        version: The version of the api on the openapi_schema.
        description: The description of the api on the openapi_schema.

    Returns:
        A function, _get_custom_openapi, that retrieves openapi_schema on the FastAPI instance, creating the schema if one does not exist.
    """

    def _get_custom_openapi():
        if app.openapi_schema:
            return app.openapi_schema

        openapi_schema = get_openapi(
            title=title,
            version=version,
            description=description,
            routes=app.routes,
        )
        app.openapi_schema = openapi_schema
        return app.openapi_schema

    return _get_custom_openapi


health_router: APIRouter = APIRouter()


@health_router.get("/health", operation_id="get_health")
async def health() -> str:
    """Retrieves the health status of the API.

    Returns:
        A string of "healthy" if the API is healthy.
    """
    return "healthy"
