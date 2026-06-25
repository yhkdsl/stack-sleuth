#!/usr/bin/env bash

set -euo pipefail

: "${TOOL_SERVER_URL:=http://localhost:8080}"
: "${TOOL_SERVER_TOKEN:=local-dev-token}"

curl --fail-with-body \
  --request POST \
  "${TOOL_SERVER_URL}/internal/tools/sql/read-only" \
  --header "Content-Type: application/json" \
  --header "X-Tool-Server-Token: ${TOOL_SERVER_TOKEN}" \
  --header "X-Trace-Id: example-read-only-query" \
  --data '{"sql":"SELECT id, account_status, profile_img FROM users WHERE id = 42"}'
