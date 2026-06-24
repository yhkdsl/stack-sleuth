# Developer Experience Content Strategy

StackSleuth is both a software project and a public explanation of how to build a bounded AI agent. This document defines the content artifacts required to demonstrate Developer Experience engineering skills alongside implementation quality.

## Goals

- Help a Java/Spring developer run and understand the project without prior agent experience.
- Explain architectural decisions and rejected alternatives, not only final code.
- Preserve reproducible problem-solving records from development.
- Publish copyable API examples that are safe to run locally.
- Show successful investigations and failure paths through CLI and dashboard evidence.
- Produce portfolio evidence that can be linked from a resume, application, or technical interview.

## Audience

Primary readers:

- Java/Spring backend developers learning OpenAI tool calling
- Developers evaluating safe access from AI agents to internal APIs and databases
- Developer Experience reviewers assessing documentation, examples, and product usability
- Open-source contributors running StackSleuth for the first time

The repository documentation is written in English for global accessibility. Blog manuscripts use Korean for the main article and include an English summary for international reviewers.

## Content Surfaces

| Surface | Purpose | Location |
| --- | --- | --- |
| README | Explain the product, current status, quickstart, and strongest evidence | `README.md` |
| Beginner tutorial | Guide a new user from clone to a replayable investigation | `docs/TUTORIAL.md` |
| Architecture docs | Explain boundaries, ownership, and design rationale | `docs/ARCHITECTURE.md` |
| Build log | Record problems, evidence, fixes, and lessons | `docs/BUILD_LOG.md` |
| Runnable examples | Provide safe requests and expected result shapes | `examples/` |
| Blog manuscripts | Turn implementation lessons into publishable technical content | `docs/articles/` |
| Demo assets | Show CLI, dashboard, replay, and guardrail behavior | `docs/assets/` |
| External publication | Improve discovery and collect reader feedback | Personal blog, DEV Community, Medium, or another public platform |

GitHub Wiki is reserved for future community-maintained FAQ, troubleshooting, recipes, and migration notes. Versioned technical content remains in the repository so it can be reviewed in pull requests with the code it explains.

## Documentation Definition of Done

A major feature issue is not complete for portfolio purposes until the associated pull request includes or updates:

1. A beginner-facing usage path with prerequisites and exact commands.
2. A short explanation of why the design was selected.
3. At least one copyable request, response, or code example.
4. A failure case or operational limitation.
5. A build-log entry when the work involved a meaningful defect, tradeoff, or debugging lesson.
6. A visual capture requirement when the change affects CLI or dashboard behavior.
7. Accurate implementation status without claiming planned behavior is complete.

Small maintenance fixes do not require a new article. They should update an existing article or build-log entry when they reveal a reusable engineering lesson.

## Article Series

| No. | Working title | Implementation dependency | Repository manuscript |
| --- | --- | --- | --- |
| 01 | Spring Boot를 AI Agent의 안전한 Tool Server로 만들기 | Spring tool server | `docs/articles/01-safe-spring-tool-server.ko.md` |
| 02 | LLM이 실행하는 SQL을 이중으로 보호하는 방법 | PostgreSQL demo and SQL guardrails | `docs/articles/02-defense-in-depth-sql-safety.ko.md` |
| 03 | OpenAI Function Calling Agent Loop 구현하기 | Python agent service | `docs/articles/03-openai-function-calling-agent-loop.ko.md` |
| 04 | Agent의 판단 과정을 React로 시각화하기 | Trace dashboard | `docs/articles/04-react-agent-trace-dashboard.ko.md` |
| 05 | AI Agent의 timeout, 무한 반복, 개인정보 문제 검증하기 | Evals and failure-mode tests | `docs/articles/05-agent-failure-modes-and-evals.ko.md` |

Each manuscript must contain:

- English summary
- intended reader and learning outcomes
- architecture or request-flow explanation
- runnable code or API example
- one failure mode and its handling
- verification evidence
- links to the relevant source files, issue, and pull request
- publication status and external URL after publication

## Publication Workflow

1. Implement and verify the feature.
2. Update the beginner tutorial and runnable examples in the same feature PR when practical.
3. Record significant debugging or design lessons in `docs/BUILD_LOG.md`.
4. Update the corresponding manuscript from `Planned` to `Draft`.
5. Capture sanitized screenshots or GIFs after the end-to-end flow works.
6. Review commands, links, secrets, personal data, and implementation claims.
7. Merge the docs-as-code version.
8. Publish the article externally and add the public URL to the manuscript and README.

## Evidence for Applications

The final portfolio should make the following claims verifiable:

- The applicant can build a full-stack agent product, not only call a model API.
- The applicant can explain complex backend and AI concepts to another developer.
- The applicant designs quickstarts, examples, error messages, and replay modes for adoption.
- The applicant records failure paths and safety constraints instead of presenting only a polished happy path.
- The applicant maintains accurate public documentation as the implementation evolves.

Evidence should be linked directly from a resume:

- repository README
- beginner tutorial
- one architecture article
- one safety or failure-mode article
- live or recorded dashboard demonstration
- representative issue and pull request showing implementation plus documentation review

## Quality Checklist

Before publishing any tutorial or article:

- All commands were rerun from a clean checkout.
- Expected output matches the current implementation.
- Planned features are labeled as planned.
- No API keys, database passwords, tokens, private logs, emails, phone numbers, or personal data appear.
- Screenshots do not expose `.env`, terminal history, account names, or unrelated applications.
- Code samples favor the smallest safe example.
- Acronyms and agent-specific concepts are explained on first use.
- The article includes at least one limitation or rejected alternative.
- English summary accurately reflects the Korean article.

