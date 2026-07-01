# StackSleuth Submission Package

Use this page when linking StackSleuth from a resume, application, recruiter
message, or interview follow-up.

## Primary Links

| Purpose | Link |
| --- | --- |
| Repository | https://github.com/yhkdsl/stack-sleuth |
| Beginner tutorial | https://github.com/yhkdsl/stack-sleuth/blob/main/docs/TUTORIAL.md |
| DX portfolio narrative | https://github.com/yhkdsl/stack-sleuth/blob/main/docs/articles/00-why-stacksleuth-is-a-dx-portfolio.ko.md |
| Architecture | https://github.com/yhkdsl/stack-sleuth/blob/main/docs/ARCHITECTURE.md |
| Build log | https://github.com/yhkdsl/stack-sleuth/blob/main/docs/BUILD_LOG.md |
| Demo assets | https://github.com/yhkdsl/stack-sleuth/tree/main/docs/assets |

## One-Line Pitch

```text
Built StackSleuth, a Spring Boot + FastAPI + React reference implementation showing how an AI agent can safely investigate backend incidents through OpenAI tool calling, read-only SQL guardrails, trace replay, and developer-focused documentation.
```

## Korean Summary

```text
StackSleuth는 AI agent가 Spring Boot 백엔드의 내부 도구를 안전하게 호출해 장애 원인을 조사하는 포트폴리오 프로젝트입니다. 단순 챗봇이 아니라 OpenAI tool calling, read-only SQL guardrail, timeout, redaction, trace replay, terminal CLI, React observability dashboard를 통해 AI에게 backend 작업을 어디까지 안전하게 위임할 수 있는지 보여줍니다.
```

## Interview Framing

```text
I focused on the boundary between model reasoning and backend execution. The model can choose tools, but Spring and PostgreSQL enforce what can actually happen. FastAPI owns the OpenAI loop and trace persistence, while the CLI and React dashboard expose the agent's decisions as inspectable evidence instead of hiding them behind a chatbot UI.
```

## Best Evidence to Mention

- Spring Boot tool server with internal auth, bounded tool contracts, and audit
  records.
- PostgreSQL read-only role plus SQL parser guardrails for defense in depth.
- Explicit FastAPI Responses API loop with timeout, max-iteration, redaction,
  and trace persistence boundaries.
- CLI that talks only to FastAPI and supports trace replay without rerunning
  OpenAI or Spring.
- React replay dashboard that shows tool calls, guardrail rejections, latency,
  token usage, redactions, and final evidence.
- Deterministic eval scenarios for successful investigation, destructive SQL
  rejection, tool timeout, and max-iteration stopping.
- Build log and article drafts that explain implementation decisions and
  failure cases.

## Demo Guidance

Prefer these safe repo assets for first-pass application review:

- `docs/assets/dashboard-replay-demo.gif`
- `docs/assets/dashboard-replay-actual.png`
- `docs/assets/terminal-demo.svg`
- `docs/assets/guardrail-rejection.svg`
- `docs/assets/architecture.svg`

Record a live terminal video only when the checklist in `docs/DEMO_SCRIPT.md`
has been completed and the terminal does not show `.env`, credentials, shell
history, local account names, browser profile menus, or unrelated applications.

## Publication Status

Repository docs and Korean article manuscripts are versioned in `docs/`.
External blog publication URLs are intentionally absent until posts are actually
published.
