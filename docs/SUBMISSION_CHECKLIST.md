# Submission Checklist

Use this before linking the project in a resume, application, or recruiter message.

## Repository

- [ ] README explains the project in the first screen.
- [ ] README says this is an agentic backend tool-calling system, not a chatbot.
- [ ] README includes architecture diagram.
- [ ] README includes quickstart.
- [ ] README includes terminal demo GIF.
- [ ] README includes trace dashboard screenshot or GIF.
- [ ] README includes guardrail rejection example.
- [ ] README links to all major docs.
- [ ] No document claims an unimplemented feature is already complete.

## Backend

- [ ] Spring Boot tool server has health, log search, and read-only SQL tools.
- [ ] Spring internal endpoints require local internal authentication.
- [ ] SQL parser blocks DDL, DML, and multi-statement input.
- [ ] Database user is read-only.
- [ ] Tool responses are deterministic JSON.
- [ ] Tool audit logs include `traceId`, `requestId`, status, latency, and rejection reason.
- [ ] Tool outputs do not include secrets.

## Agent Service

- [ ] Python FastAPI service calls the OpenAI Responses API.
- [ ] Tool schemas use strict JSON schemas where supported.
- [ ] Agent loop has max iteration limit.
- [ ] Tool calls have timeouts.
- [ ] Total request timeout is enforced.
- [ ] Trace is persisted with redaction.
- [ ] Trace replay works without calling OpenAI.
- [ ] Cost display is hidden or clearly labeled as estimated using configured pricing metadata.

## Frontend

- [ ] Dashboard is a trace viewer, not a generic chatbot UI.
- [ ] Dashboard shows original request and final answer.
- [ ] Dashboard shows ordered tool calls.
- [ ] Dashboard shows guardrail rejections.
- [ ] Dashboard shows latency and token usage.
- [ ] Dashboard labels redacted fields clearly.
- [ ] Dashboard supports sample replay without an OpenAI API key.
- [ ] Dashboard does not call Spring internal tool endpoints directly.

## Tests

- [ ] Spring unit tests pass.
- [ ] Spring integration tests with PostgreSQL pass.
- [ ] Python unit tests pass.
- [ ] Agent loop tests pass with mocked OpenAI responses.
- [ ] Frontend component tests pass.
- [ ] Playwright smoke test passes.
- [ ] Eval scenarios pass.
- [ ] Destructive SQL rejection is tested.
- [ ] Max-iteration failure is tested.
- [ ] Tool timeout is tested.

## Demo

- [ ] `make up` starts local services.
- [ ] `make demo` seeds deterministic data.
- [ ] CLI happy-path investigation works.
- [ ] CLI guardrail rejection works.
- [ ] Dashboard opens the returned trace.
- [ ] Sample replay works without API key.
- [ ] Demo recording does not expose secrets.

## Application Positioning

Use this framing after the implementation is complete and verified:

```text
I built a Spring Boot + Python FastAPI + React reference implementation showing how an AI agent can safely operate internal backend tools through OpenAI tool calling. The frontend is intentionally an agent observability dashboard rather than a generic chatbot UI: it shows tool calls, guardrail decisions, latency, token usage, redaction events, and replayable traces. I used AI-assisted frontend development for rapid iteration, then manually reviewed the result for production-minded developer experience.
```

Avoid this framing:

```text
I made a ChatGPT chatbot for server monitoring.
```
