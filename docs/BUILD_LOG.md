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

## 2026-06-25: Keep Tool APIs Bounded and Framework-Neutral

**Related work:** PR #8

**Problem:** Exposing raw Actuator output, log files, or JDBC results would couple the future agent to Spring internals and leak more operational data than each investigation step needs.

**Evidence:** The three MVP tools require different backend integrations, but the agent only needs stable JSON contracts, correlation identifiers, and predictable error codes. It does not need access to framework-specific management endpoints or database credentials.

**Root cause:** Treating an agent as a trusted application administrator would erase the boundary between reasoning and execution.

**Decision:** Publish three narrow `POST /internal/tools/**` operations with request validation and normalized response DTOs. Bind the service to loopback by default, require an internal shared token for the local MVP, compare that token without an early-exit string comparison, propagate `traceId` and `requestId`, and return structured errors without exposing implementation details.

**Verification:** Security and validation tests cover missing or invalid authentication, malformed input, correlation headers, and local binding. Spring management endpoints are not exposed, and tool responses contain bounded domain data instead of raw framework objects.

**Lesson for readers:** A tool server is an authorization and translation boundary. Stable, least-authority contracts let an agent use a Java backend without making the agent Spring-specific.

**Documentation updated:** `README.md`, `docs/ARCHITECTURE.md`, and `docs/articles/01-safe-spring-tool-server.ko.md`.

## 2026-06-25: Make Demo Incidents Deterministic Across Logs and PostgreSQL

**Related work:** PR #9

**Problem:** An investigation demo is not useful documentation when log searches and database queries produce unrelated or time-dependent evidence.

**Evidence:** The scenario needs the same three failures to appear in both the sample application log and the `error_events` table. A real system clock would eventually move those fixed events outside a request such as "the last hour."

**Root cause:** Static fixtures were initially treated as separate examples instead of one reproducible incident timeline.

**Decision:** Correlate log lines and database rows with `req-demo-4201` through `req-demo-4203`, use a configurable fixed Clock for the demo window, and keep all fixture identities synthetic. Add a fixture check that requires each request ID exactly once in each source and rejects obvious email, phone, token, and private-key patterns.

**Verification:** `infra/scripts/verify-fixtures.sh` validates correlation and sensitive-data patterns. PostgreSQL verification confirms three matching incident rows, and tool tests use the fixed instant to return deterministic recent-log results.

**Lesson for readers:** Reproducible sample data is part of Developer Experience. Readers should be able to run a tutorial later and observe the same evidence that the author documented.

**Documentation updated:** `README.md`, `docs/TUTORIAL.md`, and `docs/articles/02-defense-in-depth-sql-safety.ko.md`.

## 2026-06-25: Report Database Health Truthfully and Within a Time Budget

**Related work:** PR #9 Health API follow-up

**Problem:** The first Health API design could describe a configured DataSource as healthy without proving that PostgreSQL was reachable. A failed connection could also inherit HikariCP's long acquisition wait and make an agent investigation stall.

**Evidence:** Health review found that configuration presence and connection availability were conflated. Connection-failure testing also exposed the need for a bounded wait and a pool configuration that would not keep unnecessary idle connections alive in the local tool server.

**Root cause:** Dependency configuration was used as a proxy for dependency health, and connection-pool defaults were accepted without an agent latency budget.

**Decision:** Attempt a real read-only connection and report `available`, `unavailable`, or `not_configured`. Mark the overall result `degraded` only when the configured database is unavailable, return stable non-sensitive messages, set the connection timeout to two seconds, and set `minimumIdle` to zero.

**Verification:** Unit tests cover disabled, reachable, and unreachable database states. Testcontainers exercises the reachable path, and the current Spring suite contains 29 passing tests.

**Lesson for readers:** Health contracts must distinguish absence from failure, and every dependency check used by an agent needs an explicit time budget.

**Documentation updated:** `README.md`, `docs/TUTORIAL.md`, and `docs/articles/01-safe-spring-tool-server.ko.md`.

## 2026-06-25: Treat Documentation Drift as a CI Failure

**Related work:** PR #10

**Problem:** The documentation branch was created before PR #9 merged, so it later contained a README conflict and statements that still described database work as planned. Its recorded test count was also behind the implementation.

**Evidence:** Rebasing onto `main` exposed the conflict. A documentation validation pass then found stale implementation text, missing executable coverage for a successful SQL example, and claims that no longer matched the 29-test codebase.

**Root cause:** Documentation and implementation evolved in parallel without an automated check for their shared contracts.

**Decision:** Rebase documentation work onto the implemented baseline, add the missing successful read-only query example, and validate Markdown and shell examples in the same GitHub Actions workflow as the backend. The validator checks local links, balanced code fences, known stale claims, obvious sensitive values, and required executable examples.

**Verification:** `node infra/scripts/verify-documentation.mjs` validates 18 Markdown files, `bash -n examples/curl/*.sh` validates example syntax, the four documented curl flows were exercised against the local stack, and the PR workflow passed with the 29-test Spring suite and PostgreSQL checks.

**Lesson for readers:** Documentation is a versioned product surface. Examples and implementation-status claims should fail CI when they stop matching the software.

**Documentation updated:** `docs/CONTENT_STRATEGY.md`, `docs/TUTORIAL.md`, `examples/curl/`, and `.github/workflows/spring-tool-server-ci.yml`.
