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
```

Run the Spring tool server, then execute an example:

```bash
TOOL_SERVER_TOKEN=local-dev-token examples/curl/health.sh
```

Each script accepts `TOOL_SERVER_URL` and `TOOL_SERVER_TOKEN` from the environment.

`read-only-query.sh` expects an HTTP `200` response containing the synthetic `user_id=42` row. `rejected-sql.sh` expects HTTP `400` with `SQL_WRITE_BLOCKED`.

## Planned Examples

```text
examples/
  traces/
    null-profile-image.json
    rejected-destructive-sql.json
```

Trace fixtures will be added with the agent service and replay dashboard. The canonical beginner sequence remains in `docs/TUTORIAL.md`.
