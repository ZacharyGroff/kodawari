## Models
models is a package used to share models between kodawari services.

### Installation
models is installed using [poetry](https://python-poetry.org/docs/) with [path dependencies](https://python-poetry.org/docs/dependency-specification/#path-dependencies) in editable mode.

```console
$ poetry add --editable ./path/to/kodawari.models
```

### Usage
```python
from models.user import UserSchema

user_schema: UserSchema = UserSchema(**params)
```

