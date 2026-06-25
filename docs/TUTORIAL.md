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
- Python 3.12
- [uv](https://docs.astral.sh/uv/)
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

The PostgreSQL demo is implemented with deterministic fixtures and a database-enforced read-only tool account.

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

Run a successful investigation query, then observe the destructive-query policy boundary:

```bash
examples/curl/read-only-query.sh
examples/curl/rejected-sql.sh
```

The first request returns the synthetic `user_id=42` incident row through the restricted database account. The second returns HTTP `400` with a structured `SQL_WRITE_BLOCKED` error. The database remains unchanged.

## 5. Verify the Agent Loop Without Credentials

The Python service and HTTP API are implemented. First run the deterministic
mock path, which needs neither an OpenAI API key nor a running Spring server:

```bash
cd python-agent-service
uv sync --locked --all-groups
uv run ruff check .
uv run pytest -q --cov=app --cov-report=term-missing
uv run python ../examples/python-agent/mock_investigation.py
```

The example uses the production `AgentLoop` and `FileTraceStore` with scripted
model and tool adapters. It prints a completed trace and writes temporary data
outside the repository.

For a live run, keep the Spring server running and set an OpenAI API key plus
an explicit Responses API model available to your project:

```bash
set -a
source ../.env
set +a
uv run uvicorn app.main:app --reload --port 8000
```

In another terminal:

```bash
curl -X POST http://localhost:8000/agent/run \
  -H 'Content-Type: application/json' \
  -d '{"request":"Investigate errors from the last hour and summarize the evidence."}'
```

The expected scenario can select this tool path:

1. `search_error_logs`
2. `run_read_only_query`
3. final incident summary with trace ID

The exact calls remain a model decision, so automated tests use scripted model
responses instead of asserting nondeterministic live behavior. The terminal
CLI is still planned.

## 6. Inspect and Replay the Trace

The trace API is implemented. Replay a trace returned by `POST /agent/run`:

```bash
curl http://localhost:8000/agent/traces/<trace_id>
```

Replay reads the redacted local JSON trace and does not call OpenAI or Spring.
The React dashboard is still planned.

The dashboard will eventually show:

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

### Live agent requests return HTTP 503

Set both `OPENAI_API_KEY` and `AGENT_MODEL` before starting Uvicorn. The service
intentionally starts without credentials so trace replay remains available,
but live runs return `AGENT_NOT_CONFIGURED`.

### A live request times out or stops before an answer

Inspect the returned trace. `REQUEST_TIMEOUT` means the full request exceeded
`REQUEST_TIMEOUT_SECONDS`; `MAX_ITERATIONS_REACHED` means the model exhausted
`AGENT_MAX_ITERATIONS`. A Spring timeout appears on the individual tool result
as `TOOL_TIMEOUT`. `MODEL_RESPONSE_INCOMPLETE` records a Responses API
incomplete status such as `max_output_tokens`, while `EMPTY_MODEL_OUTPUT`
prevents an empty response from being reported as success.

Requests longer than `MAX_USER_REQUEST_CHARS` are rejected before a model call.
`MAX_OUTPUT_TOKENS` bounds each model response. The total request deadline
reserves time for trace persistence; a storage overrun returns
`TRACE_PERSISTENCE_TIMEOUT` instead of extending the request indefinitely.

## Next Reading

- [Architecture](ARCHITECTURE.md)
- [Content Strategy](CONTENT_STRATEGY.md)
- [Build Log](BUILD_LOG.md)
- [Demo Script](DEMO_SCRIPT.md)
- [Article Series](articles/README.md)
