#!/bin/bash

export PGPASSWORD=${DB_PASSWORD}
python3 deploy_migrations.py

if [ $? -ne 0 ]; then
  echo Migrations were not deployed
  exit 1
fi
