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

## 2026-06-25: Carry Stateless Reasoning Context Without Storing Responses

**Related work:** Issue #3

**Problem:** A multi-turn Responses API loop must preserve model output between tool calls, but the project should not depend on server-side response retention.

**Evidence:** OpenAI's conversation-state and reasoning guidance requires a stateless client to send prior output items again. For reasoning models with storage disabled, encrypted reasoning content must also be requested and carried forward.

**Root cause:** A simple loop that returns only `function_call_output` loses the response items that connect one reasoning turn to the next.

**Decision:** Set `store=false`, request `reasoning.encrypted_content`, append every returned output item plus the tool result to the next input, and keep the original user request at the start of the accumulated history. Disable parallel tool calls and request at most one tool call per response so execution remains auditable.

**Verification:** Mocked SDK tests inspect the exact Responses API arguments. Loop tests verify that the next model request contains the original request, previous function call, and matching function output. The integration test exercises the same continuation path through FastAPI, the Spring router, and trace replay.

**Lesson for readers:** Statelessness is not the absence of state. It moves conversation-state ownership into application code, where retention and audit behavior can be made explicit.

**Documentation updated:** `python-agent-service/README.md`, `docs/TUTORIAL.md`, and `docs/articles/03-openai-function-calling-agent-loop.ko.md`.

## 2026-06-25: Redact Secrets Without Destroying Token Metrics

**Related work:** Issue #3

**Problem:** The first recursive redaction rule treated any field name containing `token` as sensitive, which also redacted legitimate observability fields such as `totalTokens`.

**Evidence:** Trace-store tests expected usage counters to remain integers but received `[REDACTED]`.

**Root cause:** Substring matching conflated credentials with metrics. In an agent trace, `accessToken` is sensitive while `inputTokens` and `totalTokens` are operational measurements.

**Decision:** Normalize field names and compare them against an explicit credential-key set. Scan string values for API-key, bearer-token, email, and phone patterns before tool output is returned to the model, then repeat the scan immediately before persistence.

**Verification:** Redaction tests cover nested credentials and personal data while requiring usage metrics to survive unchanged. The HTTP integration test injects a synthetic email-shaped value into a mocked Spring result and verifies that the model continuation, persisted trace, and replayed trace contain `[REDACTED]`.

**Lesson for readers:** Redaction is a data-classification problem, not a keyword search. Over-redaction can silently break the observability needed to operate an agent.

**Documentation updated:** This build log and `docs/articles/03-openai-function-calling-agent-loop.ko.md`.

## 2026-06-25: Treat Model Completion and Persistence as Bounded Contracts

**Related work:** PR #11 review hardening

**Problem:** A Responses API result with `status=incomplete` could have no tool
call and an empty output string, which the first loop implementation reported
as a successful trace. The request timeout also ended before local trace
persistence, and request/output size had no explicit bound.

**Evidence:** A regression fixture with
`incomplete_details.reason=max_output_tokens` produced `status=completed`,
`finalAnswer=""`, and no error. A delayed trace store extended a request beyond
its configured deadline.

**Decision:** Preserve response status metadata in the adapter, map incomplete,
failed, and empty responses to explicit trace failures, reserve part of the
total deadline for persistence, reject oversized user requests before model
execution, and pass `MAX_OUTPUT_TOKENS` to every Responses API call.

**Verification:** Tests cover incomplete and failed responses, empty completed
responses, persistence timeout, request-length rejection, output-token
configuration, and redaction before model continuation.

**Lesson for readers:** A bounded agent must constrain the whole lifecycle, not
only the tool loop. Provider status, input size, output size, and trace storage
are all part of the runtime contract.

**Documentation updated:** `python-agent-service/README.md`,
`docs/TUTORIAL.md`, `docs/ARCHITECTURE.md`, and
`docs/articles/03-openai-function-calling-agent-loop.ko.md`.

## 2026-06-26: Preserve Both Execution and Persistence Failures

**Related work:** PR #11 review hardening

**Problem:** When agent execution and trace persistence both timed out, the
response preserved only `REQUEST_TIMEOUT` while returning a trace ID that could
not be replayed. The duration field was also finalized before persistence, and
the provider's machine-readable failed-response code was collected but unused.

**Evidence:** A combined-failure regression reproduced
`error.code=REQUEST_TIMEOUT` with no trace file. A delayed store showed that
`totalDurationMs` omitted the main persistence write.

**Decision:** Add an explicit `persisted` flag and a separate
`persistenceError`, preserve the primary execution error, finalize duration
inside the file store after its first write pass, use an execution-budget
timeout message, and include only the provider's machine-readable error code.
Provider error messages remain excluded.

**Verification:** Regression tests cover successful persistence, persistence
timeout, combined execution and persistence timeout, persisted duration, and
provider error-code propagation.

**Lesson for readers:** A trace ID is not proof that a trace exists.
Observability APIs must distinguish execution outcome from evidence durability
so clients do not offer broken replay links.

**Documentation updated:** `python-agent-service/README.md`,
`docs/TUTORIAL.md`, `docs/DEVELOPMENT_PLAN.md`, and
`docs/articles/03-openai-function-calling-agent-loop.ko.md`.

## 2026-06-27: Make the Terminal CLI a Thin Trace Client

**Related work:** Issue #4

**Problem:** The project pitch starts in the terminal, but a CLI that directly
called Spring tools would duplicate the agent service boundary and risk
turning the client into another executor.

**Evidence:** Issue #4 requires `ops-agent ask`, verbose tool output, trace
show, and trace replay. The architecture requires dashboards and clients to
call FastAPI only, because FastAPI owns model orchestration and trace records.

**Root cause:** A command-line tool can look like the natural place to put
operations logic, but in this architecture it should be a developer experience
surface over the agent API.

**Decision:** Package `ops-agent` with the Python service as a thin sync HTTP
client. `ask` calls only `POST /agent/run`; `trace show` and `trace replay`
call only `GET /agent/traces/{traceId}`. The CLI prints the final answer first,
then trace ID and compact evidence. Verbose mode expands tool calls, guardrail
rejections, redactions, and token usage. Output receives a defensive redaction
pass before it reaches the terminal.

**Verification:** CLI tests cover happy path output, verbose output, guardrail
rejection display, dashboard URL output, trace show, replay without an
agent run, structured API errors, and connection failures.

**Lesson for readers:** A good DX CLI should make the system easier to operate
without becoming a second implementation of the system. The safest client is
boring: call the public agent API, format the evidence, and preserve the
security boundary.

**Documentation updated:** `README.md`, `python-agent-service/README.md`,
`docs/TUTORIAL.md`, `docs/BUILD_LOG.md`, and
`docs/articles/03-openai-function-calling-agent-loop.ko.md`.

## 2026-06-29: Make the Frontend an Observability Surface, Not a Chatbot

**Related work:** Issue #5

**Problem:** The project needs a full-stack surface for portfolio review, but a
generic chat UI would weaken the backend/agent story by hiding tool execution
behind another message stream.

**Evidence:** Issue #5 requires original request, final answer, ordered tool
calls, guardrail rejections, redaction labels, cost/latency visibility, and
credential-free replay. Those are observability requirements, not chat
requirements.

**Root cause:** Agent demos often optimize for the final answer. StackSleuth
needs to prove that a reviewer can inspect how the answer was produced.

**Decision:** Build `web-dashboard` as a Vite + React trace viewer with
`/traces`, `/traces/{traceId}`, and `/replay`. Persisted trace pages call only
FastAPI `GET /agent/traces/{traceId}`. Replay mode renders bundled sample trace
data and does not call OpenAI, Spring, or FastAPI.

**Verification:** Component tests cover replay without network, FastAPI-only
trace loading, redaction labels, evidence rendering, missing-trace errors, and
empty state. Playwright smoke verifies the sample replay final answer, ordered
tool call, and guardrail panel. Desktop and mobile screenshots were reviewed
for text overlap and trace readability.

**Lesson for readers:** A frontend for an agent system should make the agent
auditable. The safest dashboard is a reader of redacted traces, not another
executor with access to internal tools.

**Documentation updated:** `README.md`, `docs/TUTORIAL.md`,
`docs/FRONTEND_DASHBOARD.md`, `web-dashboard/README.md`, and
`docs/articles/05-react-agent-trace-dashboard.ko.md`.

## 2026-06-29: Turn Failure Modes into Deterministic Evals

**Related work:** Issue #6

**Problem:** The project already had unit tests for individual failure modes,
but reviewers still needed one copyable command that proved the MVP handles
happy-path investigation, SQL rejection, tool timeout, and max-iteration stop.

**Evidence:** Issue #6 requires `evals/scenarios.yml`, an eval runner, expected
tool calls, guardrail events, final-answer evidence, and fixture safety.

**Root cause:** Unit tests are good engineering evidence, but they are not
always legible as a product-level safety story. A Developer Experience sample
needs a higher-level scenario runner that maps directly to the README claim.

**Decision:** Add deterministic eval scenarios that run the production
`AgentLoop` with scripted model turns and scripted Spring tool results. The
runner avoids OpenAI, Spring, PostgreSQL, and external YAML dependencies, then
asserts trace status, tool order, guardrail codes, timeout codes, error codes,
and required evidence.

**Verification:** Runner tests cover scenario coverage, happy-path tool order,
failure contracts, and `main()` success. The local runner prints four `PASS`
lines for null-profile investigation, destructive SQL rejection, tool timeout,
and max-iteration stop.

**Lesson for readers:** Evals do not have to start as a full model-quality
benchmark. For an agent MVP, the first useful eval is often a deterministic
contract suite that proves the system fails safely and preserves evidence.

**Documentation updated:** `README.md`, `docs/TUTORIAL.md`,
`docs/DEVELOPMENT_PLAN.md`, and
`docs/articles/06-agent-failure-modes-and-evals.ko.md`.

## 2026-06-29: Make Portfolio Evidence Safe and Explicit

**Related work:** Issue #7

**Problem:** The repository had the MVP implementation, but the README still
made readers scroll before seeing the strongest evidence. Demo recording was
also described as planned without a safe checked-in visual alternative.

**Evidence:** Issue #7 requires demo assets, architecture diagram, guardrail
rejection material, README final pass, beginner-path verification, and accurate
content status. Raw terminal or desktop recordings can accidentally expose
`.env`, local account names, terminal history, browser profiles, or unrelated
applications.

**Root cause:** Implementation evidence and publication evidence are related
but not identical. A working dashboard is not automatically a safe portfolio
asset, and a planned GIF should not be described as completed until it exists.

**Decision:** Add sanitized static demo frames under `docs/assets/` for the
terminal flow, dashboard replay, guardrail rejection, and architecture diagram.
Keep the README honest: the local MVP is implemented, live OpenAI runs require
user credentials, live model quality is not CI evidence, and a polished GIF or
video remains a manual publication task. Add a focused redacted guardrail trace
fixture for `SQL_WRITE_BLOCKED`.

**Verification:** Documentation validation passed across 22 Markdown files.
Fixture sensitive-data scan passed. Shell examples passed syntax checks.
Python ruff passed, Python tests passed with 55 tests and 97% coverage,
deterministic evals printed four `PASS` results, frontend lint/test/build
passed, Playwright replay smoke passed, and the Spring test suite built
successfully.

**Lesson for readers:** A portfolio demo should be safe by default. Synthetic
or replay-based assets are less flashy than raw recordings, but they give
reviewers immediate evidence without leaking local state or overstating what
has been externally published.

**Documentation updated:** `README.md`, `docs/DEMO_SCRIPT.md`,
`docs/CONTENT_STRATEGY.md`, `docs/SUBMISSION_CHECKLIST.md`,
`docs/SKILLS_AND_DOCS.md`, `docs/assets/`, `examples/README.md`,
`examples/traces/guardrail-rejection-redacted.json`, and
`docs/articles/`.
