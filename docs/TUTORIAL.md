# StackSleuth Beginner Tutorial

This tutorial is the canonical beginner path for running StackSleuth. It will grow with the implementation while keeping planned steps clearly separated from working steps.

## What You Will Build

The finished local system will contain:

1. A Spring Boot server exposing approved backend tools.
2. PostgreSQL with deterministic incident data and a read-only tool account.
3. A Python service running an OpenAI tool-calling loop.
4. A terminal CLI for starting investigations.
5. A React dashboard for inspecting and replaying agent traces.

The project is not a generic chatbot. The model receives bounded tools, while application code enforces authentication, SQL policy, timeouts, redaction, and audit records.

## Prerequisites

- Git
- Java 21
- Docker Desktop or another Docker-compatible runtime
- Python 3.12 or later, once the agent service is implemented
- Node.js, once the dashboard is implemented
- An OpenAI API key, only for live agent runs

Replay mode will be designed to work without an OpenAI API key.

## 1. Clone and Inspect the Repository

```bash
git clone https://github.com/yhkdsl/stack-sleuth.git
cd stack-sleuth
cp .env.example .env
```

Do not commit `.env`. Set local database passwords before starting PostgreSQL.

## 2. Run the Spring Tool Server Tests

```bash
./gradlew :spring-tool-server:test
```

This verifies internal authentication, request validation, SQL guardrails, log search, and audit behavior included in the current implementation.

## 3. Start the Deterministic PostgreSQL Demo

This section becomes available after the PostgreSQL demo-data pull request is merged.

```bash
docker compose --env-file .env -f infra/docker-compose.yml up -d --wait
set -a
source .env
set +a
infra/scripts/verify-fixtures.sh
infra/scripts/verify-postgres.sh
```

The verification checks deterministic row counts, the `user_id=42` null-profile incident, read-only role settings, and rejection of write operations.

## 4. Run the Spring Server

```bash
set -a
source .env
set +a
./gradlew :spring-tool-server:bootRun
```

In a second terminal, check the normalized health tool:

```bash
curl -X POST http://localhost:8080/internal/tools/health \
  -H 'Content-Type: application/json' \
  -H "X-Tool-Server-Token: ${TOOL_SERVER_TOKEN}" \
  -d '{"includeJvm":true,"includeDbPool":true}'
```

Try a destructive query to observe the policy boundary:

```bash
curl -X POST http://localhost:8080/internal/tools/sql/read-only \
  -H 'Content-Type: application/json' \
  -H "X-Tool-Server-Token: ${TOOL_SERVER_TOKEN}" \
  -d '{"sql":"DROP TABLE users"}'
```

Expected behavior: HTTP `400` with a structured `SQL_WRITE_BLOCKED` error. The database must remain unchanged.

## 5. Run a Live Agent Investigation

**Status: Planned.** This section will be activated after the Python agent service and CLI are implemented.

The intended command is:

```bash
ops-agent ask "최근 1시간 동안 에러가 있었는지 확인하고 원인을 요약해줘" --open-trace
```

The expected tool path is:

1. `search_error_logs`
2. `run_read_only_query`
3. final incident summary with trace ID

## 6. Inspect and Replay the Trace

**Status: Planned.** This section will be activated after the React dashboard is implemented.

The dashboard will show:

- original request and final answer
- ordered tool calls and results
- guardrail rejections distinct from execution failures
- redacted fields
- latency and token usage
- replay mode backed by checked-in sample trace JSON

## Troubleshooting

### Docker reports that a password is missing

Set `POSTGRES_PASSWORD` and `TOOL_DB_PASSWORD` in `.env`. Do not put real production credentials in the demo environment.

### Database credentials changed but the old password still applies

PostgreSQL initialization scripts run only when the data volume is created. Remove the local demo volume and recreate it:

```bash
docker compose --env-file .env -f infra/docker-compose.yml down -v
docker compose --env-file .env -f infra/docker-compose.yml up -d --wait
```

This command deletes only the local deterministic demo database.

### A feature described here does not exist yet

Check the implementation status in `README.md` and the relevant GitHub issue. Planned sections are intentionally retained so the tutorial evolves without misrepresenting project status.

## Next Reading

- [Architecture](ARCHITECTURE.md)
- [Content Strategy](CONTENT_STRATEGY.md)
- [Build Log](BUILD_LOG.md)
- [Demo Script](DEMO_SCRIPT.md)
- [Article Series](articles/README.md)

