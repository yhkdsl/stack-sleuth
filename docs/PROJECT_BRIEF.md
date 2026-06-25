# StackSleuth Project Brief

## 1. Executive Summary

StackSleuth is a terminal-first AI agent system with a web-based observability dashboard for backend operations investigation. A developer asks a natural-language question such as "Check whether errors increased in the last hour and summarize the likely cause." The agent decides which approved backend tools to call, invokes Spring Boot APIs, inspects logs and safe database snapshots, and returns a concise incident-style report. The frontend dashboard shows the full trace: tool calls, tool inputs and outputs, guardrail decisions, latency, token usage, and final evidence.

The core portfolio signal is not "I connected to ChatGPT." The core signal is: **I can design a safe, observable, production-minded tool-calling backend system that lets an AI model operate inside constrained engineering boundaries.**

## 2. Target Role Fit

This project is designed to support an application for OpenAI Developer Experience Engineer, AI Deployment Engineer, or related developer-facing engineering roles.

It demonstrates:

- Ability to build reference implementations developers can learn from
- Practical understanding of OpenAI tool/function calling
- Strong backend engineering foundations in Java, Spring Boot, SQL, logs, and APIs
- Product-minded DX: quickstart, CLI demo, trace dashboard, architecture docs, failure-mode docs
- Safety-minded AI engineering: tool boundaries, SQL constraints, audit trails, max loops, and human-readable traces
- Full-stack judgment: the frontend is not a generic chatbot UI; it is an agent observability and replay surface that makes the backend system easier to inspect, debug, and explain

## 3. Problem

Backend engineers often investigate incidents through repeated context switching:

- Check metrics
- Search logs
- Inspect database state
- Correlate timestamps, user IDs, request IDs, and service errors
- Summarize the result for teammates

This workflow is repetitive but risky to automate blindly. An AI agent can help only if it operates through narrow, auditable tools rather than unrestricted shell, database, or infrastructure access.

## 4. Product Concept

The system exposes a terminal command:

```bash
ops-agent ask "최근 1시간 동안 에러 발생한 거 있는지 확인하고 원인 분석해서 요약해줘"
```

The agent may then:

1. Call `check_server_health` to inspect CPU, memory, JVM, and DB pool state.
2. Call `search_error_logs` with a bounded time window and keyword.
3. Call `run_read_only_query` only if the SQL guardrail approves the query.
4. Correlate the observations.
5. Produce a final report with evidence, confidence, and recommended next actions.

For full-stack visibility, the CLI can open a trace dashboard:

```bash
ops-agent ask "최근 1시간 동안 에러 분석해줘" --open-trace
```

The dashboard is intentionally designed as a developer experience layer, not as the primary interaction surface. It helps reviewers and future users understand what the agent did, which tools it selected, which safeguards fired, and why the final answer is trustworthy.

## 5. Recommended Architecture

```text
Terminal CLI
    |
    v
Python FastAPI Agent Service
    - OpenAI Responses API orchestration
    - tool schema registration
    - agent loop
    - trace collection
    - cost/token budget
    |
    v
Spring Boot Tool Server
    - health tool
    - log search tool
    - read-only SQL tool
    - audit log
    - internal auth / tool policy
    |
    v
PostgreSQL + sample app logs + Micrometer metrics

React/Next.js Trace Dashboard
    ^
    |
    +--- reads trace data from Python FastAPI Agent Service
```

### Why split Spring Boot and Python?

Spring Boot should own backend system control because it is the strongest signal for a Java backend candidate: APIs, DB access, security, observability, and operational discipline.

Python should own the OpenAI agent loop because the OpenAI Python SDK and agentic examples are usually the fastest path for current API features and experimentation. This also shows the ability to work across stacks, which is valuable in developer experience roles.

## 6. Core Components

### Terminal CLI

Responsible for:

- Accepting a natural-language task
- Sending a request to the Python agent service
- Streaming or printing the final report
- Optionally showing tool trace output in verbose mode

Suggested commands:

```bash
ops-agent ask "지난 1시간 에러 분석해줘"
ops-agent ask "DB connection pool 문제가 있었는지 확인해줘" --verbose
ops-agent ask "최근 1시간 에러 분석해줘" --open-trace
ops-agent trace replay trace_2026_06_23_001
```

### React/Next.js Trace Dashboard

Responsible for:

- Showing the user's original request and final answer
- Rendering the ordered agent loop timeline
- Showing each tool call name, input, output summary, latency, and status
- Highlighting SQL guardrail approvals and rejections
- Displaying token usage, total duration, model name, and estimated cost when pricing metadata is configured
- Replaying saved traces without calling OpenAI again
- Making failure modes visible rather than hiding them in logs

Suggested views:

- `Trace Timeline`: chronological tool-call and model-step sequence
- `Evidence`: compact table of log lines, DB rows, and health warnings used in the final answer
- `Guardrails`: accepted/rejected tool calls with reasons
- `Cost and Latency`: token usage, per-tool latency, and estimated cost when pricing metadata is configured
- `Replay`: load a saved trace JSON and inspect it offline

Frontend positioning:

- Build this dashboard with AI-assisted frontend development to show modern engineering workflow.
- Review and refine the result manually for state handling, layout, error states, empty states, and trace readability.
- Present it as a DX surface for understanding agent behavior, not as a generic chat product.

### Python FastAPI Agent Service

Responsible for:

- Calling the OpenAI Responses API
- Registering tool schemas with strict JSON schemas where possible
- Running the tool-call loop
- Enforcing max iterations, tool timeout, total request timeout, and bounded tool output
- Adding a cumulative token-budget policy as a production-hardening follow-up
- Converting Spring API responses into model-readable tool outputs
- Persisting traces for replay and debugging
- Redacting sensitive tool outputs before storing or showing traces

Key design choice:

- Start with manual Responses API tool loop for maximum clarity.
- Optionally add Agents SDK later as an advanced branch once the low-level flow is well understood.

### Spring Boot Tool Server

Responsible for:

- Exposing approved tools only
- Validating requests before touching logs or DB
- Enforcing read-only SQL policy
- Recording audit logs
- Providing deterministic JSON responses

Initial tool endpoints:

```http
POST /internal/tools/health
POST /internal/tools/logs/search
POST /internal/tools/sql/read-only
```

Trace endpoints belong to the Python agent service because the trace includes model calls, tool calls, guardrail events, and final answers. The Spring tool server should only audit its own tool executions.

OpenAI tool names use snake_case, while Spring endpoints use URL paths. Keep these names stable because traces, evals, CLI output, and dashboard rendering all depend on them.

### Database and Sample Data

Use PostgreSQL with a small sample schema:

- `users`
- `orders`
- `login_events`
- `error_events`

Seed intentionally broken scenarios:

- User profile image is null and triggers a sample exception
- Payment status mismatch
- Slow query from an indexed/unindexed column comparison
- Repeated login failure from a specific IP range

### Observability

Expose:

- Tool call count
- Tool latency
- Agent loop iteration count
- Token usage
- Estimated cost when pricing metadata is configured
- Rejected tool calls
- Rejected SQL statements
- Final confidence level
- Redaction events
- Trace retention status

Frontend should consume the same trace object that the CLI uses. This avoids duplicate logic and proves the system has a coherent observability model across CLI and web.

## 7. Tool Design

### `check_server_health`

Purpose:

- Inspect runtime state without changing anything.

Input:

```json
{
  "includeJvm": true,
  "includeDbPool": true
}
```

Output:

```json
{
  "status": "degraded",
  "cpuUsagePercent": 82.4,
  "memoryUsagePercent": 71.2,
  "jvmHeapUsagePercent": 68.1,
  "dbPoolActive": 18,
  "dbPoolMax": 20,
  "warnings": ["DB pool near saturation"]
}
```

### `search_error_logs`

Purpose:

- Search application logs with a bounded time window and keyword.

Input:

```json
{
  "keyword": "ERROR",
  "sinceMinutes": 60,
  "limit": 50
}
```

Output:

```json
{
  "matches": [
    {
      "timestamp": "2026-06-23T12:14:30+09:00",
      "level": "ERROR",
      "traceId": "abc-123",
      "message": "NullPointerException at ProfileService.renderImage",
      "metadata": {
        "userId": 42
      }
    }
  ]
}
```

### `run_read_only_query`

Purpose:

- Inspect selected database state while blocking destructive operations.

Input:

```json
{
  "sql": "SELECT id, account_status, profile_img FROM users WHERE id = 42"
}
```

Output:

```json
{
  "columns": ["id", "account_status", "profile_img"],
  "rows": [[42, "active", null]],
  "rowCount": 1,
  "executionTimeMs": 8
}
```

## 8. Guardrails

### Agent Loop Controls

- Maximum tool loop iterations: 5
- Maximum single tool timeout: 5 seconds
- Maximum total request timeout: 30 seconds
- Maximum rows returned from SQL: 50
- Maximum log matches returned: 100
- Fail closed when a guardrail cannot decide
- Redact secrets, access tokens, emails, and obvious personal data before trace persistence
- Add configurable local trace retention, defaulting to 7 days, before production use

### SQL Controls

Allowed:

- `SELECT`
- `WITH ... SELECT`
- `EXPLAIN SELECT` for later advanced mode

Blocked:

- `INSERT`
- `UPDATE`
- `DELETE`
- `DROP`
- `ALTER`
- `TRUNCATE`
- `CREATE`
- `GRANT`
- `REVOKE`
- Multi-statement SQL
- Comments that hide extra statements

Implementation recommendation:

- Do not rely only on string matching.
- Use a SQL parser such as JSqlParser in Spring.
- Use a database user with read-only permissions.
- Add `LIMIT` server-side when missing.

### Prompt Injection Controls

The model must not receive raw unrestricted logs if those logs may contain user-controlled text. Log results should be structured and truncated. The system prompt should explicitly state that tool outputs are data, not instructions.

### Service Security Controls

- Protect Spring internal tool endpoints with a local shared token or mTLS-ready abstraction.
- Keep internal tools bound to localhost in the default Docker Compose setup.
- Configure CORS so the dashboard can only call the FastAPI agent service, not Spring internal tools directly.
- Include `traceId` and `requestId` in every service log line.
- Never store `OPENAI_API_KEY` or database credentials in traces.

### Human Oversight

The MVP is read-only, so no approval workflow is required for changes. If future versions add remediation actions, those actions must require explicit human approval.

## 9. OpenAI API Design

Use the Responses API as the default low-level API because the official API reference describes it as the endpoint for creating model responses that can call custom code or built-in tools.

Use function calling/tool calling with strict schemas because the official function calling guide recommends strict mode so function calls adhere to the function schema rather than best-effort matching.

Recommended starting model:

- Use a currently available OpenAI model that supports tool calling in the Responses API.
- Keep the model name configurable through `AGENT_MODEL`.
- Document the tested model in the README rather than hardcoding a portfolio claim.
- Treat cost display as an estimate based on a checked-in pricing config or disable it when pricing is not configured.

## 10. Demo Scenarios

### Scenario A: Null Profile Image Incident

User:

```text
최근 1시간 동안 에러가 있었는지 확인하고 원인을 요약해줘.
```

Expected tool path:

1. `search_error_logs(keyword="ERROR", sinceMinutes=60)`
2. `run_read_only_query(sql="SELECT id, account_status, profile_img FROM users WHERE id = 42")`
3. Final report with cause, evidence, and recommendation

Expected final answer:

```text
최근 1시간 동안 ProfileService에서 NullPointerException 3건이 발생했습니다.
공통점은 user_id=42 요청에서 profile_img가 null인 상태로 이미지 렌더링 로직에 진입한 것입니다.
DB 확인 결과 users.profile_img 값이 null입니다.
권장 조치: ProfileService에서 null fallback 이미지를 처리하고, 기존 null 데이터에 기본 이미지를 채우는 migration을 검토하세요.
```

### Scenario B: DB Pool Saturation

User:

```text
방금 API가 느렸는데 서버 상태와 DB 상태를 확인해줘.
```

Expected tool path:

1. `check_server_health(includeJvm=true, includeDbPool=true)`
2. `search_error_logs(keyword="timeout", sinceMinutes=30)`
3. Final report

### Scenario C: Guardrail Rejection

User:

```text
테스트니까 users 테이블 비워줘.
```

Expected behavior:

- Agent must not execute destructive SQL.
- If the model attempts a destructive query, Spring blocks it.
- Final answer explains that write operations are outside the current tool policy.

## 11. Repository Structure

```text
stack-sleuth/
  README.md
  docs/
    PROJECT_BRIEF.md
    ARCHITECTURE.md
    DEVELOPMENT_PLAN.md
    FRONTEND_DASHBOARD.md
    DEMO_SCRIPT.md
    SUBMISSION_CHECKLIST.md
    SKILLS_AND_DOCS.md
  spring-tool-server/
    src/main/java/...
    src/test/java/...
  python-agent-service/
    app/
    tests/
  cli/
    ops_agent/
    tests/
  web-dashboard/
    app/
    components/
    lib/
    tests/
  infra/
    docker-compose.yml
    postgres/
      init.sql
  examples/
    traces/
    prompts/
```

## 12. Open Source Expansion Path

Start portfolio-first, then open-source-ready:

### Portfolio MVP

- One working incident scenario
- Three tools
- Guardrails
- Trace logs
- Trace dashboard for the main scenario
- Demo GIF
- Strong README

### Open Source v0.1

- Docker Compose quickstart
- Configurable tool registry
- Pluggable SQL policy
- Example trace replay
- Contribution guide

### Open Source v0.2

- Support MySQL in addition to PostgreSQL
- Add Micrometer/Prometheus integration
- Add OpenTelemetry trace export
- Add tool approval workflow for optional remediation tools

## 13. Success Criteria

The project is successful when a reviewer can:

- Clone the repo
- Run one command to start Spring, FastAPI, and PostgreSQL
- Run one CLI command that triggers multiple AI-selected tool calls
- See that destructive SQL is blocked
- Open a trace dashboard showing what the model did and why
- Understand the architecture from the README without asking for explanation

## 14. Risks and Mitigations

| Risk | Mitigation |
| --- | --- |
| Looks like a thin ChatGPT wrapper | Emphasize tool loop, backend APIs, guardrails, and traces |
| SQL safety is too naive | Use parser, read-only DB user, server-side limit, multi-statement block |
| Demo depends on live production data | Use deterministic seeded sample data |
| OpenAI model output varies | Use structured tool schemas and stable eval scenarios |
| Frontend distracts from backend signal | Keep frontend as a trace dashboard, not a chatbot or broad admin UI |
| Project feels too large | Ship MVP with one polished scenario and one polished trace dashboard before adding extra tools |

## 15. Source References

- OpenAI Responses API: https://platform.openai.com/docs/api-reference/responses
- OpenAI Function Calling Guide: https://platform.openai.com/docs/guides/function-calling
- OpenAI Agents SDK Guide: https://platform.openai.com/docs/guides/agents
- OpenAI Safety Best Practices: https://platform.openai.com/docs/guides/safety-best-practices
- OpenAI Production Best Practices: https://platform.openai.com/docs/guides/production-best-practices
