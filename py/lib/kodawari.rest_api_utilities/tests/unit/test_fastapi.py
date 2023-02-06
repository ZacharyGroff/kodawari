from typing import Any
from unittest.mock import patch

from fastapi import FastAPI

from rest_api_utilities.fastapi import get_custom_openapi_wrapper


def test_get_custom_open_api_wrapper() -> None:
    with patch("rest_api_utilities.fastapi.get_openapi") as get_openapi_mock:
        app: FastAPI = FastAPI()
        expected_openapi_schema: dict[str, Any] = {
            "title": "My test API",
            "version": "1.0.0",
            "description": "My test description",
            "routes": app.routes,
        }
        get_openapi_mock.return_value = expected_openapi_schema

        result: dict[str, Any] = get_custom_openapi_wrapper(
            app=app,
            title=expected_openapi_schema["title"],
            version=expected_openapi_schema["version"],
            description=expected_openapi_schema["description"],
        )()

        get_openapi_mock.assert_called_once_with(**expected_openapi_schema)
        assert expected_openapi_schema == result

        get_openapi_mock.reset_mock()
        result: dict[str, Any] = get_custom_openapi_wrapper(
            app=app,
            title=expected_openapi_schema["title"],
            version=expected_openapi_schema["version"],
            description=expected_openapi_schema["description"],
        )()

        get_openapi_mock.assert_not_called()
        assert expected_openapi_schema == result
