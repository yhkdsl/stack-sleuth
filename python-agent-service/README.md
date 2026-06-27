# StackSleuth Python Agent Service

This FastAPI service owns the bounded OpenAI Responses API loop and the
redacted investigation trace. Spring Boot remains the only component allowed
to execute backend tools.

## Requirements

- Python 3.12
- [uv](https://docs.astral.sh/uv/)
- The Spring tool server for live tool execution
- An OpenAI API key and an explicit tool-capable model for live model calls

## Install and Verify

```bash
cd python-agent-service
uv sync --locked --all-groups
uv run ruff check .
uv run pytest -q --cov=app --cov-report=term-missing
```

Run the deterministic example without an API key or Spring server:

```bash
uv run python ../examples/python-agent/mock_investigation.py
```

The example uses the real agent loop and trace store with scripted model and
tool adapters. It prints a completed trace and writes the temporary trace
outside the repository.

## Run the Service

From the repository root, create a local environment file and set
`OPENAI_API_KEY`, `AGENT_MODEL`, and `TOOL_SERVER_TOKEN`:

```bash
cp .env.example .env
set -a
source .env
set +a
cd python-agent-service
uv run uvicorn app.main:app --reload --port 8000
```

`AGENT_MODEL` has no code default. Select a Responses API model available to
your project that supports function calling.

Start an investigation:

```bash
curl -X POST http://localhost:8000/agent/run \
  -H 'Content-Type: application/json' \
  -d '{"request":"Investigate errors from the last hour and summarize the evidence."}'
```

Replay a saved trace without calling OpenAI or Spring:

```bash
curl http://localhost:8000/agent/traces/<trace_id>
```

The service can start without an OpenAI API key so saved traces remain
replayable. Live `POST /agent/run` requests then return a structured HTTP `503`
configuration error.

## Terminal CLI

This package also exposes the `ops-agent` command. It is a thin client over the
FastAPI service, not a separate tool executor:

```bash
uv run ops-agent ask "Investigate errors from the last hour"
uv run ops-agent ask "Investigate errors from the last hour" --verbose
uv run ops-agent ask "Investigate errors from the last hour" --open-trace
uv run ops-agent trace show <trace_id>
uv run ops-agent trace replay <trace_id>
```

Environment variables:

- `STACKSLEUTH_AGENT_URL`, default `http://localhost:8000`
- `STACKSLEUTH_DASHBOARD_URL`, default `http://localhost:3000`
- `STACKSLEUTH_AGENT_TIMEOUT_SECONDS`, default `10`

`ask` calls only `POST /agent/run`. `trace show` and `trace replay` call only
`GET /agent/traces/{traceId}`. The CLI never calls Spring internal endpoints.
`--open-trace` prints the dashboard trace URL; the dashboard implementation is
still planned. Terminal output applies a defensive redaction pass before
printing trace data or structured errors.

## Trace Persistence Contract

Every agent response includes two persistence fields:

- `persisted` is `true` only after the redacted trace has been atomically moved
  to its replay location.
- `persistenceError` is normally `null`. If persistence misses the total
  request deadline, it contains `TRACE_PERSISTENCE_TIMEOUT`.

The primary `error` preserves the investigation failure. For example, if model
execution and trace persistence both time out, `error.code` remains
`REQUEST_TIMEOUT`, while `persistenceError.code` reports
`TRACE_PERSISTENCE_TIMEOUT` and `persisted` is `false`. Clients must check
`persisted` before offering a replay link.

`totalDurationMs` is finalized by the trace store after its first write pass and
is included in the persisted JSON. This captures model and tool execution,
queueing, redaction, serialization, and the main persistence write. The final
atomic replacement is intentionally not timed recursively into the JSON value.

## Failure Contract

| Condition | HTTP | Primary code | Persisted trace |
| --- | ---: | --- | --- |
| Live model is not configured | 503 | `AGENT_NOT_CONFIGURED` | No trace is created |
| User request exceeds the configured limit | 413 | `REQUEST_TOO_LARGE` | No trace is created |
| Agent execution budget is exhausted | 504 | `REQUEST_TIMEOUT` | Check `persisted` |
| Model returns `incomplete` | 409 | `MODEL_RESPONSE_INCOMPLETE` | Normally yes |
| Model returns `failed` | 502 | `MODEL_RESPONSE_FAILED` | Normally yes |
| Completed response has no answer or tool call | 409 | `EMPTY_MODEL_OUTPUT` | Normally yes |
| Iteration limit is exhausted | 409 | `MAX_ITERATIONS_REACHED` | Normally yes |
| Trace persistence misses the deadline | 409, 502, or 504 | Original failure, or `TRACE_PERSISTENCE_TIMEOUT` | No |

For a failed Responses API result, `error.providerCode` preserves the
provider's non-sensitive machine-readable code when one is present. Provider
error messages are not copied into the trace.

## Safety Boundaries

- At most one tool call is requested per model response.
- Model iterations, each Spring request, and the full agent request have
  independent limits.
- User requests are limited by `MAX_USER_REQUEST_CHARS`, and each model
  response is limited by `MAX_OUTPUT_TOKENS`.
- Only the three registered read-only tools can be routed.
- Tool output is treated as untrusted data and is size-bounded.
- API keys, credentials, tokens, email addresses, and phone numbers are
  redacted before tool output is returned to OpenAI. Trace persistence applies
  the same recursive redaction again as a defense-in-depth check.
- OpenAI `incomplete` and failed response states never become successful empty
  answers. The total request deadline also reserves time for trace persistence.
- OpenAI response storage is disabled. Stateless reasoning items are carried
  forward using encrypted reasoning content as documented by OpenAI.

Local JSON trace storage is suitable for the MVP and replay development. It
does not yet provide retention policies, multi-process coordination, or
production durability.
