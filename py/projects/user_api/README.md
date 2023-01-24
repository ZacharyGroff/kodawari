## User API
The User API is implemented in Python using [Fast API](https://fastapi.tiangolo.com/). It provides CRUD routes for managing UserSchema objects, stored in Cassandra. Because Kodawari is currently just a mock back-end, the POST route in the User API is currently not protected. In the real world, this POST route would be only accessible to internal services that are responsible for creating accounts.

### Run in Local Container
To run the User API locally, ensure you have $CASSANDRA_CLUSTER_NAME, $KODAWARI_SECRET_KEY, and $USER_API_PORT environment variables set before executing the following command:

```console
$ ./${KODAWARI_ROOT}/tools/scripts/start_user_api.sh
```

### Generate OpenApi Spec
To generate an OpenApi spec, ensure you have $KODAWARI_ROOT and $USER_API_PORT environment variables set before running the following script:

```console
$ ./${KODAWARI_ROOT}/tools/scripts/generate_open_api_spec_user_api.sh
```
