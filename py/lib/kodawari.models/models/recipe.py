from pydantic import BaseModel, Field, Required


class RecipeSchema(BaseModel):
    id: int = Field(
        default=Required, gt=0, description="The unique identifier for a recipe"
    )
    name: str = Field(
        default=Required,
        max_length=100,
        description="The user provided name for a recipe",
    )
    created_at: int = Field(
        default=Required,
        gt=1674484829053,
        lt=9999999999999,
        description="The time the recipe was created, expressed as a unix timestamp in milliseconds",
    )
    author_id: int = Field(
        default=Required,
        gt=0,
        description="The unique identifer for the author of a recipe",
    )
    description: str = Field(
        default="",
        max_length=1000,
        description="The user provided description for the unique characteristics that define this recipe",
    )
    views: int = Field(
        default=0, gt=-1, description="The number of times the recipe has been viewed"
    )
    subscribers: int = Field(
        default=0, gt=-1, description="The number of users subscribed to this recipe"
    )
    vote_diff: int = Field(
        default=0,
        description="The differential of upvotes minus downvotes for the recipe",
    )


class VariationSchema(BaseModel):
    id: int = Field(
        default=Required, gt=0, description="The unique identifier for a variation"
    )
    recipe_id: int = Field(
        default=Required, gt=0, description="The unique identifier for the base recipe"
    )
    name: str = Field(
        default=Required,
        max_length=100,
        description="The user provided name for a variation",
    )
    created_at: int = Field(
        default=Required,
        gt=1674484829053,
        lt=9999999999999,
        description="The time the variation was created, expressed as a unix timestamp in milliseconds",
    )
    ingredients: list[str] = Field(
        default=[], max_length=50, description="The ingredients used in the variation"
    )
    process: str = Field(
        default="",
        max_length=1000,
        description="A description of the steps taken to produce the variation",
    )
    notes: str = Field(
        default="",
        max_length=1000,
        description="A description of how the variation tastes, smells, and/or looks in comparison to the base recipe",
    )
    views: int = Field(
        default=0,
        gt=-1,
        description="The number of times the variation has been viewed",
    )
    vote_diff: int = Field(
        default=0,
        description="The differential of upvotes minus downvotes for the variation",
    )
