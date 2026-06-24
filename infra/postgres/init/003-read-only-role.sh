#!/usr/bin/env bash

set -euo pipefail

: "${POSTGRES_DB:?POSTGRES_DB must be set}"
: "${POSTGRES_USER:?POSTGRES_USER must be set}"
: "${TOOL_DB_USER:?TOOL_DB_USER must be set}"
: "${TOOL_DB_PASSWORD:?TOOL_DB_PASSWORD must be set}"

psql \
  --username "${POSTGRES_USER}" \
  --dbname "${POSTGRES_DB}" \
  --set=database_name="${POSTGRES_DB}" \
  --set=tool_db_user="${TOOL_DB_USER}" \
  --set=tool_db_password="${TOOL_DB_PASSWORD}" <<'SQL'
CREATE ROLE :"tool_db_user"
    LOGIN
    PASSWORD :'tool_db_password'
    NOSUPERUSER
    NOCREATEDB
    NOCREATEROLE
    NOINHERIT
    NOREPLICATION
    NOBYPASSRLS;

ALTER ROLE :"tool_db_user" SET default_transaction_read_only = on;
ALTER ROLE :"tool_db_user" SET statement_timeout = '5s';
ALTER ROLE :"tool_db_user" SET lock_timeout = '1s';
ALTER ROLE :"tool_db_user" SET idle_in_transaction_session_timeout = '5s';

REVOKE ALL ON DATABASE :"database_name" FROM PUBLIC;
GRANT CONNECT ON DATABASE :"database_name" TO :"tool_db_user";

REVOKE CREATE ON SCHEMA public FROM PUBLIC;
GRANT USAGE ON SCHEMA public TO :"tool_db_user";
GRANT SELECT ON ALL TABLES IN SCHEMA public TO :"tool_db_user";
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT SELECT ON TABLES TO :"tool_db_user";
SQL
