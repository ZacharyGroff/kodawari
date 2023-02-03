#!/bin/bash

WORKFLOW_NAME=$1

if [[ -z $WORKFLOW_NAME ]]; then
    echo -e "${RED}No workflow entered... Testing all workflows...${NO_COLOR}"
	act -W .github/workflows --container-architecture linux/amd64 --rm
else
	act -W .github/workflows/$WORKFLOW_NAME.yaml --container-architecture linux/amd64 --rm
fi

docker builder prune --force
