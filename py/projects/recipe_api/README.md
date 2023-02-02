## Recipe API
The Recipe API is implemented in Python using [Fast API](https://fastapi.tiangolo.com/). It provides CRUD routes for managing RecipeSchema and VariationSchema objects, stored in Cassandra.

### Run in Local Container
To run the Recipe API locally, ensure you have $CASSANDRA_CLUSTER_NAME, $KODAWARI_SECRET_KEY, $RECIPE_API_INSTANCE_ID, and $RECIPE_API_PORT environment variables set before executing the following command:

```console
$ ./${KODAWARI_ROOT}/tools/scripts/start_recipe_api.sh
```

### Generate OpenApi Spec
To generate an OpenApi spec, ensure you have $KODAWARI_ROOT, $RECIPE_API_INSTANCE_ID, and $RECIPE_API_PORT environment variables set before running the following script:

```console
$ ./${KODAWARI_ROOT}/tools/scripts/generate_open_api_spec_recipe_api.sh
```
