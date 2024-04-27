#!/bin/bash

if [ -z $(git tag --points-at) ]; then
  export BRANCH_NAME=$(git branch --show-current)
else
  export BRANCH_NAME=$(git tag --points-at)
fi
