from typing import Any

from pydantic import BaseModel, Field, Required

_recipe_name_description = "The user provided name for a recipe"
_variation_name_description = "The user provided name for a variation"


def _get_name_field(default: Any, description: str) -> Any:
    return Field(
        default=default,
        max_length=100,
        description=description,
    )


_recipe_description_description: str = "The user provided description for the unique characteristics that define this recipe"
_variation_notes_description: str = "A description of how the variation tastes, smells, and/or looks in comparison to the base recipe"
_variation_process_description: str = (
    "A description of the steps taken to produce the variation"
)


def _get_description_field(default: Any, description: str) -> Any:
    return Field(
        default=default,
        max_length=1000,
        description=description,
    )


_recipe_id_description: str = "The unique identifier for a recipe"
_recipe_author_id_description: str = "The unique identifer for the author of a recipe"
_variation_author_id_description: str = (
    "The unique identifer for the variation of a recipe"
)
_variation_id_description: str = "The unique identifier for a variation"


def _get_id_field(default: Any, description: str) -> Any:
    return Field(
        default=default,
        gt=0,
        description=description,
    )


def _get_views_field(default: Any, description: str) -> Any:
    return Field(default=default, gt=-1, description=description)


def _get_vote_diff_field(default: Any, description: str) -> Any:
    return Field(
        default=default,
        description=description,
    )


def _get_created_at_field() -> Any:
    return Field(
        default=Required,
        gt=1674484829053,
        lt=9999999999999,
        description="The resource creation time, expressed as a unix timestamp in milliseconds",
    )


class RecipeSchema(BaseModel):
    """A base recipe.

    Attributes:
        id: The unique identifier for a recipe
        author_id: The unique identifer for the author of a recipe
        created_at: The resource creation time, expressed as a unix timestamp in milliseconds
        name: The user provided name for a recipe
        description: The user provided description for the unique characteristics that define this recipe
        views: The number of times the recipe has been viewed
        subscribers: The number of users subscribed to this recipe_id
        vote_diff: The differential of upvotes minus downvotes for the recipe
    """

    id: int = _get_id_field(Required, _recipe_id_description)
    author_id: int = _get_id_field(Required, _recipe_author_id_description)
    created_at: int = _get_created_at_field()
    name: str = _get_name_field(Required, _recipe_name_description)
    description: str = _get_description_field(Required, _recipe_description_description)
    views: int = _get_views_field(0, "The number of times the recipe has been viewed")
    subscribers: int = Field(
        default=0, gt=-1, description="The number of users subscribed to this recipe"
    )
    vote_diff: int = _get_vote_diff_field(
        0, "The differential of upvotes minus downvotes for the recipe"
    )


class RecipeCreateRequest(BaseModel):
    """The required request body for creating a RecipeSchema object.

    Attributes:
        name: The user provided name for a recipe
        description: The user provided description for the unique characteristics that define this recipe
    """

    name: str = _get_name_field(Required, _recipe_name_description)
    description: str = _get_description_field("", _recipe_description_description)


class RecipePatchRequest(BaseModel):
    """The required request body for patching a RecipeSchema object.

    Attributes:
        name: The user provided name for a recipe
        description: The user provided description for the unique characteristics that define this recipe
    """

    name: str = _get_name_field(None, _recipe_name_description)
    description: str = _get_description_field(None, _recipe_description_description)


def _get_ingredients_field(default: Any) -> Any:
    return Field(
        default=default,
        max_length=50,
        description="The ingredients used in the variation",
    )


class VariationSchema(BaseModel):
    """A variation of a base recipe.

    Attributes:
        id: The unique identifier for a variation
        author_id: The unique identifer for the author of a recipe
        created_at: The resource creation time, expressed as a unix timestamp in milliseconds
        recipe_id: The unique identifer for the recipe
        name: The user provided name for a variation
        ingredients: The ingredients used in the variation
        process: A description of the steps taken to produce the variation
        notes: A description of how the variation tastes, smells, and/or looks in comparison to the base recipe
        views: The number of times the recipe has been viewed
        vote_diff: The differential of upvotes minus downvotes for the recipe
    """

    id: int = _get_id_field(Required, _variation_id_description)
    author_id: int = _get_id_field(Required, _variation_author_id_description)
    created_at: int = _get_created_at_field()
    recipe_id: int = _get_id_field(Required, _recipe_id_description)
    name: str = _get_name_field(Required, _variation_name_description)
    ingredients: list[str] = _get_ingredients_field([])
    process: str = _get_description_field("", _variation_process_description)
    notes: str = _get_description_field("", _variation_notes_description)
    views: int = _get_views_field(
        0, "The number of times the variation has been viewed"
    )
    vote_diff: int = _get_vote_diff_field(
        0, "The differential of upvotes minus downvotes for the variation"
    )


class VariationCreateRequest(BaseModel):
    """The required request body for creating a VariationSchema object.

    Attributes:
        recipe_id: The unique identifer for the recipe
        name: The user provided name for a variation
        ingredients: The ingredients used in the variation
        process: A description of the steps taken to produce the variation
        notes: A description of how the variation tastes, smells, and/or looks in comparison to the base recipe
    """

    recipe_id: int = _get_id_field(Required, _recipe_id_description)
    name: str = _get_name_field(Required, _variation_name_description)
    ingredients: list[str] = _get_ingredients_field([])
    process: str = _get_description_field("", _variation_process_description)
    notes: str = _get_description_field("", _variation_notes_description)


class VariationPatchRequest(BaseModel):
    """The required request body for patching a VariationSchema object.

    Attributes:
        name: The user provided name for a variation
        ingredients: The ingredients used in the variation
        process: A description of the steps taken to produce the variation
        notes: A description of how the variation tastes, smells, and/or looks in comparison to the base recipe
    """

    name: str = _get_name_field(None, _variation_name_description)
    ingredients: list[str] = _get_ingredients_field(None)
    process: str = _get_description_field(None, _variation_process_description)
    notes: str = _get_description_field(None, _variation_notes_description)
