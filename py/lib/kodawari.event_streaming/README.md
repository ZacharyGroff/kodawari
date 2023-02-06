## Event Streaming
event_streaming is a package used to manage event streaming within kodawari services.

### Installation
event_streaming is installed using [poetry](https://python-poetry.org/docs/) with [path dependencies](https://python-poetry.org/docs/dependency-specification/#path-dependencies) in editable mode.

```console
$ poetry add --editable ./path/to/kodawari.event_streaming
```

### Usage
```python
from event_streaming.models import RecipeEvent, RecipeEventType

recipe_event: RecipeEvent = RecipeEvent(event_type=RecipeEventType.VIEWED, actor_id=42, recipe_id=78)
```

