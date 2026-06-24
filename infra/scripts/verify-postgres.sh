#!/usr/bin/env bash

set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
compose_file="${repo_root}/infra/docker-compose.yml"

: "${POSTGRES_DB:=stacksleuth}"
: "${POSTGRES_USER:=stacksleuth_owner}"
: "${POSTGRES_PASSWORD:?POSTGRES_PASSWORD must be set}"
: "${TOOL_DB_USER:=stacksleuth_reader}"
: "${TOOL_DB_PASSWORD:?TOOL_DB_PASSWORD must be set}"

compose() {
  docker compose -f "${compose_file}" "$@"
}

owner_query() {
  compose exec -T \
    --env "PGPASSWORD=${POSTGRES_PASSWORD}" \
    postgres psql \
    --host 127.0.0.1 \
    --username "${POSTGRES_USER}" \
    --dbname "${POSTGRES_DB}" \
    --tuples-only \
    --no-align \
    --command "$1"
}

reader_query() {
  compose exec -T \
    --env "PGPASSWORD=${TOOL_DB_PASSWORD}" \
    postgres psql \
    --host 127.0.0.1 \
    --username "${TOOL_DB_USER}" \
    --dbname "${POSTGRES_DB}" \
    --tuples-only \
    --no-align \
    --command "$1"
}

assert_equals() {
  local expected="$1"
  local actual="$2"
  local description="$3"

  if [[ "${actual}" != "${expected}" ]]; then
    printf 'FAIL: %s (expected %s, got %s)\n' "${description}" "${expected}" "${actual}" >&2
    exit 1
  fi
}

assert_rejected() {
  local sql="$1"
  local description="$2"

  if reader_query "${sql}" >/dev/null 2>&1; then
    printf 'FAIL: read-only role allowed %s\n' "${description}" >&2
    exit 1
  fi
}

assert_equals "4" "$(owner_query "SELECT count(*) FROM information_schema.tables WHERE table_schema = 'public' AND table_name IN ('users', 'orders', 'login_events', 'error_events');" | tr -d '[:space:]')" "demo table count"
assert_equals "4" "$(owner_query "SELECT count(*) FROM users;" | tr -d '[:space:]')" "users seed count"
assert_equals "5" "$(owner_query "SELECT count(*) FROM orders;" | tr -d '[:space:]')" "orders seed count"
assert_equals "5" "$(owner_query "SELECT count(*) FROM login_events;" | tr -d '[:space:]')" "login events seed count"
assert_equals "3" "$(owner_query "SELECT count(*) FROM error_events;" | tr -d '[:space:]')" "error events seed count"
assert_equals "42|active|" "$(owner_query "SELECT id, account_status, profile_img FROM users WHERE id = 42;" | tr -d '[:space:]')" "null profile image incident"
assert_equals "3" "$(reader_query "SELECT count(*) FROM error_events WHERE user_id = 42;" | tr -d '[:space:]')" "reader can inspect incident evidence"
assert_equals "on" "$(reader_query "SHOW default_transaction_read_only;" | tr -d '[:space:]')" "reader defaults to read-only transactions"
assert_equals "5s" "$(reader_query "SHOW statement_timeout;" | tr -d '[:space:]')" "reader statement timeout"

assert_rejected "INSERT INTO users (id, username, account_status) VALUES (999, 'blocked-user', 'active');" "INSERT"
assert_rejected "UPDATE users SET account_status = 'disabled' WHERE id = 42;" "UPDATE"
assert_rejected "DELETE FROM users WHERE id = 42;" "DELETE"
assert_rejected "DROP TABLE error_events;" "DROP"
assert_rejected "ALTER TABLE users ADD COLUMN blocked_column text;" "ALTER"

assert_equals "4" "$(owner_query "SELECT count(*) FROM users;" | tr -d '[:space:]')" "seed remains unchanged after rejected writes"

printf 'PostgreSQL demo data and read-only role verification passed.\n'
