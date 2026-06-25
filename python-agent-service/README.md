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
