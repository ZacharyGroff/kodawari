## Models
A package providing database access utilities for kodawari utilities.

### Installation
models is installed using [poetry](https://python-poetry.org/docs/) with [path dependencies](https://python-poetry.org/docs/dependency-specification/#path-dependencies) in editable mode.

```console
$ poetry add --editable ./path/to/kodawari.database
```

### Usage
```python
from database.cassandra import get_cassandra_session, Session

session: Session = get_cassandra_session()
```

