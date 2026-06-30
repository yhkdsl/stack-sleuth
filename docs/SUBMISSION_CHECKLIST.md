# Submission Checklist

Use this before linking the project in a resume, application, or recruiter message.

## Current Repository Snapshot

As of issue #7, the repository contains safe static demo frames, an architecture
diagram, copyable examples, deterministic evals, and draft Korean article
manuscripts with English summaries. External blog publication URLs and a real
terminal GIF/video remain manual publication tasks and should not be claimed as
complete until they exist.

## Repository

- [ ] README explains the project in the first screen.
- [ ] README says this is an agentic backend tool-calling system, not a chatbot.
- [ ] README includes architecture diagram.
- [ ] README includes quickstart.
- [ ] README includes terminal demo GIF or a clearly labeled sanitized static demo frame.
- [ ] README includes trace dashboard screenshot or GIF.
- [ ] README includes guardrail rejection example.
- [ ] README links to all major docs.
- [ ] No document claims an unimplemented feature is already complete.

## Developer Experience Content

- [ ] `docs/TUTORIAL.md` works from a clean clone and explains prerequisites.
- [ ] Tutorial commands include expected behavior and troubleshooting.
- [ ] `docs/CONTENT_STRATEGY.md` reflects the actual publication status.
- [ ] `docs/BUILD_LOG.md` contains evidence-based problem-solving entries.
- [ ] `examples/` contains safe, copyable requests and trace samples.
- [ ] Architecture decisions explain why the selected boundaries were chosen.
- [ ] At least one article explains a failure path, not only the happy path.
- [ ] Korean manuscripts contain accurate English summaries.
- [ ] Implemented articles link to relevant source files, issues, and pull requests.
- [ ] Planned articles are visibly labeled as planned.
- [ ] Published external URLs are linked back to their repository manuscripts.

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

- [ ] `docker compose --env-file .env -f infra/docker-compose.yml up -d --wait` starts local PostgreSQL fixtures.
- [ ] `infra/scripts/verify-postgres.sh` verifies deterministic demo data.
- [ ] CLI happy-path investigation works.
- [ ] CLI guardrail rejection works.
- [ ] Dashboard opens the returned trace.
- [ ] Sample replay works without API key.
- [ ] Demo recording does not expose secrets.
- [ ] Screenshots and GIFs do not expose `.env`, terminal history, account names, or unrelated applications.

## Public Writing Evidence

- [ ] Article 00: DX portfolio narrative is published or submission-ready.
- [ ] Article 01: safe Spring tool server is published or submission-ready.
- [ ] Article 02: defense-in-depth SQL safety is published or submission-ready.
- [ ] Article 03: OpenAI function-calling agent loop is published or submission-ready.
- [ ] Article 04: terminal CLI trace replay is published or submission-ready.
- [ ] Article 05: React trace dashboard is published or submission-ready.
- [ ] Article 06: failure modes and evals is published or submission-ready.
- [ ] Resume links directly to the strongest tutorial, architecture article, and demo.

## Application Positioning

Use this framing after the implementation is complete and verified:

```text
I built a Spring Boot + Python FastAPI + React reference implementation showing how an AI agent can safely operate internal backend tools through OpenAI tool calling. The frontend is intentionally an agent observability dashboard rather than a generic chatbot UI: it shows tool calls, guardrail decisions, latency, token usage, redaction events, and replayable traces. I used AI-assisted frontend development for rapid iteration, then manually reviewed the result for production-minded developer experience.
```

Avoid this framing:

```text
I made a ChatGPT chatbot for server monitoring.
```
