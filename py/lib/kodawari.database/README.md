## Models
A package providing database access utilities for kodawari utilities.

### Installation
models is installed using [poetry](https://python-poetry.org/docs/) with [path dependencies](https://python-poetry.org/docs/dependency-specification/#path-dependencies) in editable mode.

```console
$ poetry add --editable ./path/to/kodawari.database -E cassandra
```

### Usage
```python
from acsylla import Session
from database.cassandra import get_cassandra_session

session: Session = get_cassandra_session()
```

