#!/bin/bash
docker-compose -f ${KODAWARI_ROOT}/tools/docker/docker-compose.yaml down -v --rmi all --remove-orphans
docker builder prune --force
