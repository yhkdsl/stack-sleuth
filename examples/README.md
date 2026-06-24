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
    rejected-sql.sh
```

Run the Spring tool server, then execute an example:

```bash
TOOL_SERVER_TOKEN=local-dev-token examples/curl/health.sh
```

Each script accepts `TOOL_SERVER_URL` and `TOOL_SERVER_TOKEN` from the environment.

## Planned Examples

```text
examples/
  curl/
    read-only-query.sh
  traces/
    null-profile-image.json
    rejected-destructive-sql.json
```

Database-backed queries and trace fixtures will be added with the feature that makes them executable. The canonical beginner sequence remains in `docs/TUTORIAL.md`.

