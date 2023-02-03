#!/bin/bash
docker-compose -f ${KODAWARI_ROOT}/tools/docker/docker-compose.yaml rm recipe_api -s -f -v
