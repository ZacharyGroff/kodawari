#!/bin/bash
docker-compose -f ${KODAWARI_ROOT}/tools/docker/docker-compose.yaml build user_api && docker-compose -f ${KODAWARI_ROOT}/tools/docker/docker-compose.yaml up -d user_api
