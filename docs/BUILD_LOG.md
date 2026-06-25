# StackSleuth Build Log

This log captures reusable engineering lessons from implementation. It is not a daily diary. Each entry records a concrete problem, evidence, decision, verification, and documentation impact.

## Entry Format

```text
Date:
Related issue or PR:
Problem:
Evidence:
Root cause:
Decision:
Verification:
Lesson for readers:
Documentation updated:
```

## 2026-06-24: Keep Agent Traces Out of the Spring Tool Server

**Related work:** Initial architecture review

**Problem:** An early endpoint list placed `GET /internal/tools/traces/{traceId}` in the Spring service.

**Evidence:** A complete trace contains model calls, tool calls, guardrail results, usage, redactions, and the final answer. Spring owns only tool execution and cannot assemble that lifecycle.

**Root cause:** The first design grouped operational data by backend technology instead of by domain ownership.

**Decision:** The Python agent service owns trace creation, persistence, and retrieval. Spring emits bounded tool results and audit events.

**Verification:** Architecture, frontend, and development-plan documents use FastAPI as the dashboard-facing trace API. The dashboard never calls Spring internal endpoints directly.

**Lesson for readers:** Service ownership should follow the lifecycle of the data. A component that sees only one step should not own the aggregate record.

**Documentation updated:** `docs/ARCHITECTURE.md`, `docs/FRONTEND_DASHBOARD.md`, and `docs/DEVELOPMENT_PLAN.md`.

## 2026-06-24: Enforce Read-Only SQL at Two Boundaries

**Related work:** Issue #1 and Issue #2

**Problem:** Parser validation alone cannot be the final security boundary for model-generated SQL.

**Evidence:** Application policies can contain parser gaps or regressions. The database can independently deny writes even when application validation fails.

**Root cause:** Treating input validation as authorization would leave a single point of failure.

**Decision:** Use JSqlParser to allow one bounded `SELECT`, then execute it through a PostgreSQL role with read-only defaults, `SELECT` grants, and statement timeouts.

**Verification:** Unit tests cover unsafe SQL shapes. Database verification attempts `INSERT`, `UPDATE`, `DELETE`, `DROP`, and `ALTER` through the reader account and requires every operation to fail.

**Lesson for readers:** Parser checks explain intent and produce useful errors; database privileges enforce authority. Agent systems need both.

**Documentation updated:** `docs/articles/02-defense-in-depth-sql-safety.ko.md`.

## 2026-06-25: Distinguish Guardrail Rejection from Tool Failure

**Related work:** PR #9 follow-up commit `8646552`

**Problem:** A database execution error returned HTTP `502` but was recorded in the audit stream as `rejected`.

**Evidence:** A regression test queried a missing table and observed `expected failed, but was rejected`.

**Root cause:** `ToolController` classified every `ToolException` as a policy rejection without considering its HTTP status.

**Decision:** Classify `4xx` tool exceptions as `rejected` and server-side tool exceptions as `failed`.

**Verification:** The new integration test first failed against the original behavior, then passed after the minimal classification change. The Spring suite had 26 passing tests at that commit; subsequent Health API coverage increased the current suite to 29.

**Lesson for readers:** Observability terminology is part of the product contract. A policy decision and an infrastructure failure demand different operator responses.

**Documentation updated:** This build log; the trace-dashboard article will reuse this distinction when its UI is implemented.
