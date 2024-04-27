#!/bin/bash

source "./scripts/prepare_env.sh"

docker build -t "languagebot-db-creator:${BRANCH_NAME}" ./db/
docker build -f ./deploy/Dockerfile -t "languagebot-service:${BRANCH_NAME}" .
