## Authentication
Authentication is a package utilized by Kodawari APIs for authenticating access tokens. Authentication is mostly out of scope for Kodawari, as it is currently represents a mock of a social media back-end.

As it stands, Kodawari APIs only expect a Bearer Token with an id claim and an expiry claim to be passed along with requests. The id claim will currently represent the internal id of a user in the Kodawari platform. This package will be expanded if a front-end is ever developed for Kodawari and the id claim will no longer be used to identify a user.


### Installation
___
Authentication is installed using [poetry](https://python-poetry.org/docs/) with [path dependencies](https://python-poetry.org/docs/dependency-specification/#path-dependencies) in editable mode.

```console
$ poetry add --editable ./path/to/kodawari.authentication
```

### Usage
___
```python
from authentication.authentication import BearerClaims, authenticate
from fastapi import FastAPI
app = FastAPI()

@app.get('/')
async def my_get_route(bearer_claims: BearerClaims = Depends(authenticate)):
    ...
```
