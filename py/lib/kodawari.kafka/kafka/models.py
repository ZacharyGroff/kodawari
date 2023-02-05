from enum import Enum, auto
from json import JSONEncoder

from pydantic import BaseModel, Field, Required


class RecipeEventType(Enum):
    """The type of event occurring in the Recipe API.

    Attributes:
        VIEWED: 1
        CREATED: 2
        MODIFIED: 3
        DELETED: 4
    """

    VIEWED = auto()
    CREATED = auto()
    MODIFIED = auto()
    DELETED = auto()


class RecipeEvent(BaseModel):
    """An event that occurred in the Recipe API.

    Attributes:
        event_type: The type of event occurring in the Recipe API
        actor_id: The unique identifier for the user performing the event
        recipe_id: The unique identifier for a recipe
    """

    event_type: RecipeEventType = Field(
        default=Required, description="The type of event occurring in the Recipe API"
    )
    actor_id: int = Field(
        default=Required,
        gt=0,
        description="The unique identifier for the user performing the event",
    )
    recipe_id: int = Field(
        default=Required,
        gt=0,
        description="The unique identifier for a recipe",
    )


class RecipeEventEncoder(JSONEncoder):
    """A class for encoding a RecipeEvent.

    Inherits from JSONEncoder and overrides default method to handle encoding of enum field.
    """

    def default(self, recipe_event: RecipeEvent):
        """Returns a json-encodable dictionary, representing a RecipeEvent.

        Args:
            recipe_event: The RecipeEvent to encode.

        Returns: A json-encodable dictionary.
        """
        recipe_event_dict = recipe_event.dict()
        recipe_event_dict["event_type"] = recipe_event_dict["event_type"].value
        return recipe_event_dict
