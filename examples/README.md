# StackSleuth Examples

This directory contains copyable, non-sensitive examples for tutorials and API documentation.

## Rules

- Examples must run against deterministic local fixtures.
- Never include real API keys, database passwords, access tokens, emails, phone numbers, or private logs.
- Use documentation IP ranges and synthetic identifiers.
- Include the command, expected status, and a minimal response shape.
- Keep live OpenAI examples separate from replay or mocked examples.

## Available Examples

```text
examples/
  curl/
    health.sh
    search-logs.sh
    read-only-query.sh
    rejected-sql.sh
  python-agent/
    mock_investigation.py
  traces/
    null-profile-image.json
```

Run the Spring tool server, then execute an example:

```bash
TOOL_SERVER_TOKEN=local-dev-token examples/curl/health.sh
```

Each script accepts `TOOL_SERVER_URL` and `TOOL_SERVER_TOKEN` from the environment.

`read-only-query.sh` expects an HTTP `200` response containing the synthetic `user_id=42` row. `rejected-sql.sh` expects HTTP `400` with `SQL_WRITE_BLOCKED`.

Run a complete mocked agent loop without an OpenAI API key or a running Spring
server:

```bash
cd python-agent-service
uv run python ../examples/python-agent/mock_investigation.py
```

The example uses the production loop and trace store with scripted adapters.
It prints a completed, redacted trace and writes only to a temporary directory.

Run deterministic eval scenarios without OpenAI, Spring, or PostgreSQL:

```bash
uv run python ../evals/run_evals.py
```

The eval runner uses `evals/scenarios.yml` and writes local traces under
`var/eval-traces` by default.

## Trace Fixtures

```text
examples/
  traces/
    null-profile-image.json
```

`null-profile-image.json` is the canonical dashboard replay fixture. Additional
guardrail trace fixtures can be added as demo assets. The canonical beginner
sequence remains in `docs/TUTORIAL.md`.
