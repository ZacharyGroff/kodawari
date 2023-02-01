#!/bin/bash
docker-compose -f ${KODAWARI_ROOT}/tools/docker/docker-compose.yaml build recipe_api && docker-compose -f ${KODAWARI_ROOT}/tools/docker/docker-compose.yaml up -d recipe_api
