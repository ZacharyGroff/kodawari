from typing import Any

from pytest import fixture

from models.recipe import RecipeEvent, RecipeEventType, RecipeSchema, VariationSchema


@fixture
def expected_recipe_schema() -> dict[str, Any]:
    return {
        "id": 1,
        "name": "my recipe name",
        "created_at": 1674484829054,
        "author_id": 2,
        "description": "my recipe description",
        "views": 3,
        "subscribers": 4,
        "vote_diff": -1,
    }


def test_recipe_schema_success(expected_recipe_schema) -> None:
    recipe_schema: RecipeSchema = RecipeSchema(**expected_recipe_schema)

    assert expected_recipe_schema["id"] == recipe_schema.id
    assert expected_recipe_schema["name"] == recipe_schema.name
    assert expected_recipe_schema["created_at"] == recipe_schema.created_at
    assert expected_recipe_schema["author_id"] == recipe_schema.author_id
    assert expected_recipe_schema["description"] == recipe_schema.description
    assert expected_recipe_schema["views"] == recipe_schema.views
    assert expected_recipe_schema["subscribers"] == recipe_schema.subscribers
    assert expected_recipe_schema["vote_diff"] == recipe_schema.vote_diff


@fixture
def expected_variation_schema() -> dict[str, Any]:
    return {
        "id": 1,
        "author_id": 2,
        "recipe_id": 3,
        "name": "my variation name",
        "created_at": 1674484829054,
        "ingredients": ["beans", "rice"],
        "process": "do it like this",
        "notes": "it was awful",
        "views": 4,
        "vote_diff": -1,
    }


def test_variation_schema_success(expected_variation_schema) -> None:
    variation_schema: VariationSchema = VariationSchema(**expected_variation_schema)

    assert expected_variation_schema["id"] == variation_schema.id
    assert expected_variation_schema["recipe_id"] == variation_schema.recipe_id
    assert expected_variation_schema["name"] == variation_schema.name
    assert expected_variation_schema["created_at"] == variation_schema.created_at
    assert expected_variation_schema["ingredients"] == variation_schema.ingredients
    assert expected_variation_schema["process"] == variation_schema.process
    assert expected_variation_schema["notes"] == variation_schema.notes
    assert expected_variation_schema["views"] == variation_schema.views
    assert expected_variation_schema["vote_diff"] == variation_schema.vote_diff


@fixture
def expected_recipe_event() -> dict[str, Any]:
    return {
        "event_type": RecipeEventType.CREATED,
        "actor_id": 1,
        "recipe_id": 2,
    }


def test_recipe_event_success(expected_recipe_event) -> None:
    recipe_event: RecipeEvent = RecipeEvent(**expected_recipe_event)

    assert expected_recipe_event["event_type"] == recipe_event.event_type
    assert expected_recipe_event["actor_id"] == recipe_event.actor_id
    assert expected_recipe_event["recipe_id"] == recipe_event.recipe_id
