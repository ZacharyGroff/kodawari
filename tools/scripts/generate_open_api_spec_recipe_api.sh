#!/bin/bash

docker-compose -f ${KODAWARI_ROOT}/tools/docker/docker-compose.yaml build recipe_api && docker-compose -f ${KODAWARI_ROOT}/tools/docker/docker-compose.yaml up -d recipe_api 
while [[ "$(curl -s -o /dev/null -w ''%{http_code}'' localhost:${RECIPE_API_PORT}/health)" != "200" ]];
do 
	echo "Waiting for health endpoint to return healthy..."
	sleep 5;
done
curl localhost:${RECIPE_API_PORT}/openapi.json > ${KODAWARI_ROOT}/py/projects/user_api/openapi.json
docker-compose -f ${KODAWARI_ROOT}/tools/docker/docker-compose.yaml down
