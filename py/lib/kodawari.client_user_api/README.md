## User API Client 
client_user_api is a manually implemented client for kodawari.user_api.

### Installation
client_user_api is installed using [poetry](https://python-poetry.org/docs/) with [path dependencies](https://python-poetry.org/docs/dependency-specification/#path-dependencies) in editable mode.

```console
$ poetry add --editable ./path/to/kodawari.client_user_api
```

### Usage
```python
import aiohttp

from client_user_api.client import Client, ResponseMeta

async with aiohttp.ClientSession() as session:
	client: Client = Client(session, api_base_url)
	response_meta: ResponseMeta = await client.get_health()
	if response_meta.status_code == 200:
		print("healthy")
```

