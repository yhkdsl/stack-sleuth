#!/usr/bin/env bash

set -euo pipefail

: "${TOOL_SERVER_URL:=http://localhost:8080}"
: "${TOOL_SERVER_TOKEN:=local-dev-token}"

response_file="$(mktemp)"
trap 'rm -f "${response_file}"' EXIT

status_code="$(
  curl --silent --show-error \
    --output "${response_file}" \
    --write-out "%{http_code}" \
    --request POST \
    "${TOOL_SERVER_URL}/internal/tools/sql/read-only" \
    --header "Content-Type: application/json" \
    --header "X-Tool-Server-Token: ${TOOL_SERVER_TOKEN}" \
    --header "X-Trace-Id: example-rejected-sql" \
    --data '{"sql":"DROP TABLE users"}'
)"

cat "${response_file}"
printf '\n'

if [[ "${status_code}" != "400" ]]; then
  printf 'Expected HTTP 400, received %s\n' "${status_code}" >&2
  exit 1
fi

