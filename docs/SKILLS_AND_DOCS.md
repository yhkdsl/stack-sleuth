# Skills and Docs Checklist

This file lists the skills, concepts, and reference documents needed to build StackSleuth well enough for a serious portfolio submission and possible open-source release.

## 1. OpenAI and Agentic AI Skills

### Required

- Responses API fundamentals
- Function/tool calling
- JSON Schema for tool parameters
- Strict tool schemas
- Agent loop design
- Tool result handling
- Prompt injection awareness
- Token and cost budgeting
- Trace-driven debugging
- Secret and PII redaction for traces

### Nice to Have

- Agents SDK concepts
- Streaming responses
- Evaluation workflows
- Prompt caching and latency optimization
- OpenTelemetry integration for agent traces

### Official Docs

- Responses API: https://developers.openai.com/api/reference/resources/responses/methods/create
- Function calling: https://developers.openai.com/api/docs/guides/function-calling
- Agents SDK: https://developers.openai.com/api/docs/guides/agents
- Safety best practices: https://developers.openai.com/api/docs/guides/safety-best-practices
- Production best practices: https://developers.openai.com/api/docs/guides/production-best-practices

## 2. Frontend and AI-Assisted UI Skills

### Required

- React
- TypeScript
- Vite
- Component-driven UI design
- API data fetching
- Loading, empty, and error states
- Responsive layout
- Accessible status indicators
- Trace/timeline visualization
- AI-assisted frontend iteration with manual review

### Important Implementation Topics

- The dashboard is an observability surface, not a chatbot UI.
- Use the backend trace schema directly instead of inventing a separate frontend data model.
- Keep raw JSON and SQL collapsible.
- Highlight guardrail rejections distinctly from ordinary tool failures.
- Provide sample replay mode so users can inspect the dashboard without an OpenAI API key.
- Show estimated cost only when pricing metadata is configured.
- Clearly label redacted fields.

### Docs

- React: https://react.dev/
- Vite: https://vite.dev/
- TypeScript: https://www.typescriptlang.org/docs/
- Playwright: https://playwright.dev/
- Vitest: https://vitest.dev/

## 3. Java and Spring Backend Skills

### Required

- Java 21
- Spring Boot 3.x
- REST controller design
- DTO validation with Jakarta Validation
- Exception handling with `@ControllerAdvice`
- Spring profiles
- Spring Actuator
- Actuator-to-safe-DTO mapping
- JDBC or JPA read queries
- Testcontainers
- JUnit 5
- Integration testing

### Important Implementation Topics

- Internal API design
- Internal service authentication
- Read-only database users
- Request/response DTOs
- Timeout handling
- Structured logging
- Audit logging
- Secret and PII redaction
- Micrometer metrics
- Secure configuration through environment variables
- Avoiding raw Actuator exposure to the model or dashboard

### Docs

- Spring Boot Reference: https://docs.spring.io/spring-boot/docs/current/reference/html/
- Spring Actuator: https://docs.spring.io/spring-boot/reference/actuator/index.html
- Testcontainers Java: https://java.testcontainers.org/
- JSqlParser: https://jsqlparser.github.io/JSqlParser/

## 4. Python Backend Skills

### Required

- Python 3.12+
- FastAPI
- Pydantic models
- HTTPX async client
- OpenAI Python SDK
- pytest
- Mocking external HTTP calls
- Environment-based config

### Important Implementation Topics

- Agent loop state machine
- Tool router abstraction
- Trace persistence
- Timeout and retry policy
- Structured error responses
- CLI-friendly response format
- Dashboard-friendly trace response format
- Trace redaction before persistence

### Docs

- FastAPI: https://fastapi.tiangolo.com/
- Pydantic: https://docs.pydantic.dev/
- HTTPX: https://www.python-httpx.org/
- pytest: https://docs.pytest.org/

## 5. Database and SQL Safety Skills

### Required

- PostgreSQL basics
- Read-only DB roles
- SQL parser-based validation
- Query timeout
- Row limits
- Safe result serialization
- Seed data design

### Guardrail Checklist

- Block non-SELECT statements.
- Block multi-statement SQL.
- Block DDL and DML.
- Block comments if the parser cannot safely handle them.
- Enforce a maximum row count.
- Enforce query timeout.
- Use a read-only database account.
- Log rejected SQL with reason and trace ID.
- Never include DB credentials or secrets in tool outputs.

### Docs

- PostgreSQL Roles and Privileges: https://www.postgresql.org/docs/current/user-manag.html
- PostgreSQL `statement_timeout`: https://www.postgresql.org/docs/current/runtime-config-client.html

## 6. DevOps and Local DX Skills

### Required

- Docker Compose
- `.env.example` hygiene
- GitHub Actions CI
- Makefile or task runner
- Local quickstart documentation
- Local-only internal service defaults

### Useful Commands to Provide

```bash
make up
make test
make eval
make dashboard
make demo
make down
```

### Docs

- Docker Compose: https://docs.docker.com/compose/
- GitHub Actions: https://docs.github.com/en/actions

## 7. Testing Strategy

### Spring Tests

- Unit tests for SQL policy.
- Unit tests for log parsing.
- Controller tests for validation errors.
- Integration tests with Testcontainers PostgreSQL.

### Python Tests

- Unit tests for tool schemas.
- Unit tests for agent loop state transitions.
- Mocked OpenAI response tests.
- Mocked Spring tool server tests.
- Trace serialization tests.

### Frontend Tests

- Component test for final answer rendering.
- Component test for tool timeline rendering.
- Component test for guardrail rejection rendering.
- Component test for replay mode.
- Component test for redacted fields.
- Component test for unavailable estimated cost.
- Playwright smoke test for sample trace page.

### End-to-End Tests

- Null profile image scenario.
- DB pool warning scenario.
- Destructive SQL rejection scenario.
- Max-iteration failure scenario.
- Dashboard opens the saved trace for the null profile image scenario.

## 8. Portfolio and Writing Skills

### Required Communication Skills

- Docs-as-code workflow using branches and pull requests
- Beginner-oriented tutorial writing
- Architecture decision and tradeoff explanation
- Reproducible debugging narratives
- Minimal, copyable, and safe code examples
- Screenshot and GIF preparation without secret exposure
- Korean technical writing with accurate English summaries
- External publication and feedback tracking

### Required Artifacts

- README with quickstart
- Beginner tutorial that starts from a clean clone
- Architecture diagram
- Demo GIF
- Tool trace example
- Trace dashboard GIF
- AI-assisted frontend development note
- Guardrail failure example
- Design tradeoff section
- Blog-style build note
- Build log containing evidence, root cause, fix, and lesson
- Runnable examples under `examples/`
- Five-part article series under `docs/articles/`

### Writing Angle

The writing should make this point clear:

```text
This project shows how to give an AI model useful backend capabilities without giving it unsafe backend authority.
```

Secondary writing point:

```text
The frontend is intentionally a trace and replay dashboard so developers can inspect agent behavior, not a generic chat interface.
```

### Suggested Blog Post Title

```text
Building a Safe Tool-Calling AI Agent for Java Spring Backend Operations
```

### Planned Article Series

1. `Spring Boot를 AI Agent의 안전한 Tool Server로 만들기`
2. `LLM이 실행하는 SQL을 이중으로 보호하는 방법`
3. `OpenAI Function Calling Agent Loop 구현하기`
4. `Agent의 판단 과정을 React로 시각화하기`
5. `AI Agent의 timeout, 무한 반복, 개인정보 문제 검증하기`

Repository manuscripts use Korean bodies with English summaries. The canonical files live under `docs/articles/` and are published externally only after the related implementation and verification are complete.

### Content Completion Rule

For every major feature:

- Update `docs/TUTORIAL.md`.
- Add a safe request, response, or code example.
- Explain the selected design and a limitation or rejected alternative.
- Add a `docs/BUILD_LOG.md` entry when the work produced a reusable lesson.
- Update the related article status and evidence.
- Capture sanitized visuals for CLI or dashboard behavior.
- Keep planned and implemented behavior visibly separate.

Frontend-focused companion title:

```text
Why My AI Agent Frontend Is a Trace Dashboard, Not a Chatbot
```

### Suggested README Tagline

```text
A production-minded reference implementation for safe OpenAI tool calling in Java/Spring backend systems.
```

## 9. Study Order

1. OpenAI Responses API and function calling
2. Spring Boot tool server endpoints
3. PostgreSQL read-only user and SQL parser validation
4. FastAPI agent loop
5. Trace design
6. CLI design
7. React trace dashboard
8. Eval scenarios
9. README/demo polish

## 10. Avoid These Early

- Building a broad admin dashboard before the trace dashboard works
- Adding write/remediation tools before read-only safety is proven
- Supporting many databases before PostgreSQL is polished
- Building multi-agent orchestration before one agent loop is reliable
- Hiding failure cases from the README

## 11. Minimum Hiring-Signal Checklist

Before submitting this project, make sure the repo proves:

- You understand OpenAI tool calling.
- You can build clean Spring Boot APIs.
- You can build a focused full-stack DX surface.
- You can design AI guardrails.
- You can make a developer-friendly quickstart.
- You can explain tradeoffs clearly.
- You can test failure modes, not only happy paths.
