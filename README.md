# StackSleuth

StackSleuth is a portfolio-grade reference implementation plan for Java/Spring backend developers who want to demonstrate production-minded OpenAI tool calling.

The project concept is simple: a developer types an operations question in a terminal, and an AI agent investigates the backend by safely calling approved Spring Boot tools such as server health checks, error-log search, and read-only SQL inspection. A web dashboard then visualizes the agent trace so engineers can inspect tool calls, guardrail decisions, latency, token usage, and final evidence. The goal is not to build another chatbot. The goal is to show how to delegate bounded backend investigation work to an AI agent with guardrails, auditability, and developer-friendly documentation.

## Positioning

**One-line pitch:** An agentic ops copilot for backend tool calling.

**Current status:** MVP implementation in progress. The Spring Boot tool server and deterministic PostgreSQL demo data are implemented; the Python agent service, CLI, and dashboard are still planned.

**What this demonstrates:**

- OpenAI Responses API tool calling and agent loop design
- Spring Boot as a secure backend tool server
- Python FastAPI as a lightweight OpenAI orchestration service
- React/Next.js as an agent observability and replay dashboard
- SQL safety controls, max-iteration limits, timeout handling, and audit logs
- AI-assisted frontend development with human-reviewed DX, state handling, and trace readability
- Developer experience artifacts: quickstart, diagrams, demo scenarios, failure cases, trace dashboard, and design rationale

## Documents

- [Project Brief](docs/PROJECT_BRIEF.md)
- [Architecture](docs/ARCHITECTURE.md)
- [Development Plan](docs/DEVELOPMENT_PLAN.md)
- [Frontend Dashboard Plan](docs/FRONTEND_DASHBOARD.md)
- [Demo Script](docs/DEMO_SCRIPT.md)
- [Submission Checklist](docs/SUBMISSION_CHECKLIST.md)
- [Skills and Docs Checklist](docs/SKILLS_AND_DOCS.md)
- [Beginner Tutorial](docs/TUTORIAL.md)
- [Developer Experience Content Strategy](docs/CONTENT_STRATEGY.md)
- [Build Log](docs/BUILD_LOG.md)
- [Korean Article Series with English Summaries](docs/articles/README.md)

## Planned Quickstart

The implementation should eventually support this local flow:

```bash
cp .env.example .env
make up
make demo
ops-agent ask "최근 1시간 에러 분석해줘" --open-trace
```

Expected result:

- The CLI prints an incident-style answer.
- The agent calls log search and read-only SQL tools.
- The dashboard opens a replayable trace.
- Destructive SQL requests are blocked and visible in the trace.

## Implementation Status

| Area | Status |
| --- | --- |
| Product brief | Documented |
| Architecture | Documented |
| Spring Boot tool server | Initial implementation complete: internal auth, health tool, log-search endpoint, database-backed read-only SQL, audit sink, and tests |
| PostgreSQL demo data | Implemented: Docker Compose, deterministic fixtures, correlated sample logs, and database-enforced read-only role |
| Python FastAPI agent service | Not started |
| CLI | Not started |
| React/Next.js trace dashboard | Not started |
| Demo recording and trace-replay assets | Not started |
| Beginner tutorial and DX content program | Structure and initial manuscripts documented; publication evidence is still in progress |

## Spring Tool Server

The Spring Boot tool server lives in `spring-tool-server`.

Run the server tests:

```bash
./gradlew :spring-tool-server:test
```

Create a local `.env`, set both database passwords, and start PostgreSQL:

```bash
cp .env.example .env
docker compose --env-file .env -f infra/docker-compose.yml up -d --wait
set -a
source .env
set +a
infra/scripts/verify-postgres.sh
```

Run the server locally with the same environment loaded:

```bash
./gradlew :spring-tool-server:bootRun
```

The example `.env` fixes the tool-server clock at `2026-06-24T03:00:00Z` so the checked-in incident remains inside a deterministic 60-minute demo window. Clear `TOOL_SERVER_CLOCK_INSTANT` to use the real UTC clock.

Check the health tool:

```bash
curl -X POST http://localhost:8080/internal/tools/health \
  -H 'Content-Type: application/json' \
  -H 'X-Tool-Server-Token: local-dev-token' \
  -d '{"includeJvm":true,"includeDbPool":true}'
```

The SQL endpoint applies parser-based read-only guardrails before executing through the restricted `TOOL_DB_USER` account. If `TOOL_DB_ENABLED` is false, it returns a structured `database_not_configured` response without attempting a connection.

Verify the seeded null-profile incident:

```bash
curl -X POST http://localhost:8080/internal/tools/sql/read-only \
  -H 'Content-Type: application/json' \
  -H "X-Tool-Server-Token: ${TOOL_SERVER_TOKEN}" \
  -d '{"sql":"SELECT id, account_status, profile_img FROM users WHERE id = 42"}'
```

## Intended Audience

This repository is designed for:

- OpenAI Developer Experience / AI Deployment Engineer portfolio review
- Java Spring backend engineers learning agentic tool calling
- Teams exploring safe AI access to internal tools
- Future open-source contributors who want a practical agent backend template

## Official OpenAI References

- Responses API: https://platform.openai.com/docs/api-reference/responses
- Function calling: https://platform.openai.com/docs/guides/function-calling
- Agents SDK: https://platform.openai.com/docs/guides/agents
- Safety best practices: https://platform.openai.com/docs/guides/safety-best-practices
- Production best practices: https://platform.openai.com/docs/guides/production-best-practices
