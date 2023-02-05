from json import dumps
from typing import Any

from pytest import fixture

from kafka.models import RecipeEvent, RecipeEventEncoder, RecipeEventType


@fixture
def expected_recipe_event() -> dict[str, Any]:
    return {
        "event_type": RecipeEventType.VIEWED,
        "actor_id": 4,
        "recipe_id": 5,
    }


def test_recipe_event_success(expected_recipe_event) -> None:
    recipe_event: RecipeEvent = RecipeEvent(**expected_recipe_event)

    assert expected_recipe_event["event_type"] == recipe_event.event_type
    assert expected_recipe_event["actor_id"] == recipe_event.actor_id
    assert expected_recipe_event["recipe_id"] == recipe_event.recipe_id


def test_recipe_event_encoder(expected_recipe_event) -> None:
    expected: str = '{"event_type": 1, "actor_id": 4, "recipe_id": 5}'
    recipe_event: RecipeEvent = RecipeEvent(**expected_recipe_event)
    assert expected == dumps(recipe_event, cls=RecipeEventEncoder)
