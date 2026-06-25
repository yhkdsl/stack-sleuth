#!/usr/bin/env bash

set -euo pipefail

: "${TOOL_SERVER_URL:=http://localhost:8080}"
: "${TOOL_SERVER_TOKEN:=local-dev-token}"

curl --fail-with-body \
  --request POST \
  "${TOOL_SERVER_URL}/internal/tools/logs/search" \
  --header "Content-Type: application/json" \
  --header "X-Tool-Server-Token: ${TOOL_SERVER_TOKEN}" \
  --header "X-Trace-Id: example-log-search" \
  --data '{"keyword":"ERROR","sinceMinutes":1440,"limit":10}'

