## Logging Utilities
logging_utilities is a package used to centralize all logging logic. Currently a decision has not been made on log monitoring and alerting technology, but having all logging logic centralized will allow us to quickly implement any log management tool we decide on in the future.

### Installation
logging_utilities is installed using [poetry](https://python-poetry.org/docs/) with [path dependencies](https://python-poetry.org/docs/dependency-specification/#path-dependencies) in editable mode.

```console
$ poetry add --editable ./path/to/kodawari.logging_utilities
```

### Usage
```python
from logging_utilities.utilities import get_logger

logger: logging.Logger = get_logger(__name__, logging.DEBUG)
logger.debug(f'Failed to authorize request with given credentials: {credentials}')
```

