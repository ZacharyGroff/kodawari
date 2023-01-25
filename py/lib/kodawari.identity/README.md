## Identity
identity is a package used to manage user identities within kodawari services. The most notable feature of this package is the id_generator function, which generates an identifier similar to a [snowflake](https://en.wikipedia.org/wiki/Snowflake_ID), as described in Twitter's blog post [Annoncing Snowflake](https://blog.twitter.com/engineering/en_us/a/2010/announcing-snowflake).

### Installation
identity is installed using [poetry](https://python-poetry.org/docs/) with [path dependencies](https://python-poetry.org/docs/dependency-specification/#path-dependencies) in editable mode.

```console
$ poetry add --editable ./path/to/kodawari.identity
```

### Usage
```python
from identity.utilities import id_generator

machine_id: int = 42
generator: Generator[int, None, None] = id_generator(machine_id)
id: int = next(generator)
```

