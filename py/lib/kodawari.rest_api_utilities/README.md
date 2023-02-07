## Rest API Utilities
rest_api_utilities is a package for housing utilities that implement common rest api functionality.

### Installation
rest_api_utilities is installed using [poetry](https://python-poetry.org/docs/) with [path dependencies](https://python-poetry.org/docs/dependency-specification/#path-dependencies) in editable mode.

```console
$ poetry add --editable ./path/to/kodawari.rest_api_utilities
```

### Usage
```python
from fastapi import FastAPI
from rest_api_utilities.fastapi import health_router

app: FastAPI = FastAPI()
app.include_router(health_router)
```

