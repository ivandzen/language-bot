FROM ubuntu:24.04 AS base

RUN apt update && apt install -y ca-certificates
RUN apt install -y python3 python3-pip
RUN apt install -y postgresql-client
RUN pip3 install psycopg2-binary --break-system-packages

COPY deploy_schema.sh \
    deploy_migrations.py /opt/

COPY migrations/* /opt/migrations/

RUN pip3 install requests --break-system-packages
WORKDIR /opt
