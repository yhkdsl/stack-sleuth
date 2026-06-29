# Architecture

## System Goal

StackSleuth gives an AI model useful backend investigation capabilities without giving it unrestricted backend authority. The model can only act through explicitly registered, read-only tools exposed by the Spring Boot tool server.

## High-Level Flow

```text
Developer
  |
  | natural-language task
  v
Terminal CLI
  |
  | POST /agent/run
  v
Python FastAPI Agent Service
  |
  | OpenAI Responses API with tool schemas
  v
OpenAI model
  |
  | tool call request
  v
Python tool router
  |
  | authenticated internal HTTP
  v
Spring Boot Tool Server
  |
  | read-only access
  v
PostgreSQL + sample logs + Micrometer/Actuator data

Python FastAPI Agent Service
  |
  | persisted redacted trace
  v
Vite + React Trace Dashboard
```

## Service Responsibilities

### Terminal CLI

- Accepts developer tasks.
- Sends requests to the agent service.
- Prints the final answer.
- Shows compact trace output with `--verbose`.
- Opens or prints the trace dashboard URL with `--open-trace`.

### Python FastAPI Agent Service

- Owns OpenAI API interaction.
- Registers tool schemas.
- Runs the agent loop.
- Enforces max iterations, tool timeouts, total timeout, and bounded tool output.
- Leaves a cumulative token-budget policy as a planned production hardening step.
- Routes approved tool calls to Spring.
- Redacts secrets and obvious personal data before trace persistence.
- Owns trace APIs such as `GET /agent/traces/{traceId}`.

### Spring Boot Tool Server

- Owns backend tool execution.
- Exposes only approved internal tools.
- Enforces DTO validation and read-only SQL policy.
- Uses a read-only database account.
- Audits tool execution with `traceId`, `requestId`, tool name, status, latency, and rejection reason.
- Does not own model traces or final agent answers.

### Vite + React Trace Dashboard

- Reads trace data from the FastAPI agent service.
- Visualizes model steps, tool calls, guardrails, evidence, latency, token usage, and final answer.
- Supports replay from sample trace JSON without an OpenAI API key.
- Never calls Spring internal tool endpoints directly.

## Tool Boundary

Initial tools:

```http
POST /internal/tools/health
POST /internal/tools/logs/search
POST /internal/tools/sql/read-only
```

The model never gets direct DB, shell, file-system, or infrastructure credentials. It can only request these tools through strict schemas and the Python router.

## Trace Ownership

The Python agent service owns traces because it sees the full workflow:

- User request
- OpenAI model responses
- Tool call requests
- Spring tool results
- Guardrail rejections
- Redaction events
- Usage metadata
- Final answer

Spring keeps its own audit logs, but those are not the same as agent traces.

## Security Model

MVP controls:

- Spring internal tools require a shared internal token in local development.
- Spring internal tools are bound to localhost or Docker network by default.
- Dashboard calls only FastAPI, not Spring.
- CORS allows only the dashboard origin to call FastAPI.
- SQL execution uses parser validation and a read-only DB user.
- Raw Actuator endpoints are not exposed to the model or dashboard; Spring returns a normalized health DTO.
- Tool results redact API keys, DB credentials, access tokens, emails, and
  obvious personal data before model continuation. Trace persistence repeats
  the same scan as a defense-in-depth check.
- Tool outputs are treated as untrusted data, not model instructions.

Future hardening:

- Replace shared token with mTLS or service identity.
- Add OpenTelemetry trace export.
- Add configurable trace retention and deletion.
- Add human approval workflow only if write/remediation tools are introduced.

## Failure Handling

Expected failures should be visible, not hidden:

- SQL blocked by guardrail
- Tool timeout
- Tool server unavailable
- OpenAI API error
- OpenAI incomplete or failed response
- Empty model response
- Max agent iterations reached
- Total request or trace-persistence timeout
- Trace redaction applied
- Pricing metadata unavailable

The CLI and dashboard should both show the trace ID so a failed investigation can be inspected.

## Design Tradeoffs

### Why CLI first?

The target user is a backend engineer or infrastructure-minded developer. A terminal workflow feels closer to real operations work and avoids making the project look like a generic chatbot.

### Why add a frontend?

The frontend proves full-stack capability and makes agent behavior understandable. It is scoped as a trace dashboard so it strengthens the backend/AI architecture instead of distracting from it.

### Why Python for the agent loop?

Python is a practical choice for OpenAI SDK iteration and agent examples. Spring remains the system-of-record for backend control, validation, DB access, and operational safety.

### Why not write tools?

The MVP is read-only because the portfolio signal is safe delegation. Write/remediation actions would require a human approval workflow and should come after read-only behavior is proven.
