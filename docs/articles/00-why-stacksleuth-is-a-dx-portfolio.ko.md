# OpenAI Developer Experience Engineer 지원을 위해 StackSleuth를 어떻게 설계했는가

- **Publication status:** Portfolio narrative draft
- **Related implementation:** Whole StackSleuth repository
- **External URL:** Not published

## English Summary

StackSleuth is designed as a Developer Experience portfolio project, not only
as a backend demo. It shows how a Java/Spring backend engineer can build and
explain a bounded AI agent system: Spring owns safe internal tools, FastAPI owns
OpenAI orchestration and trace persistence, the terminal CLI exposes a focused
developer workflow, and the planned React dashboard will turn agent traces into
inspectable evidence. The repository intentionally pairs implementation with
tutorials, build logs, failure cases, and Korean blog manuscripts with English
summaries so reviewers can evaluate both engineering judgment and the ability
to teach other developers.

## 왜 이 프로젝트를 만들었는가

OpenAI Developer Experience Engineer에게 필요한 역량은 "API를 호출할 줄 안다"에서
끝나지 않는다. 좋은 DX 엔지니어는 새로운 기술을 실제 개발자가 이해하고, 실행하고,
안전하게 확장할 수 있는 형태로 바꿔야 한다.

StackSleuth는 그 역량을 보여주기 위해 설계한 포트폴리오 프로젝트다. 주제는
일반적인 챗봇이 아니라, AI agent가 내부 backend tool을 제한된 권한으로 호출해
문제를 조사하는 시스템이다.

```text
Developer question
  -> Terminal CLI
  -> FastAPI Agent Service
  -> OpenAI tool-calling loop
  -> Spring Boot Tool Server
  -> PostgreSQL and logs
  -> Redacted trace
  -> CLI answer today, dashboard replay in the planned frontend
```

핵심은 "AI가 DB를 조회한다"가 아니다. 핵심은 애플리케이션이 어디까지 AI에게
위임하고, 어디에서 막고, 어떻게 사람이 검토할 수 있게 만드는지다.

## 포트폴리오 목표

이 프로젝트가 보여주려는 것은 네 가지다.

1. Java/Spring backend 강점을 AI agent architecture에 연결할 수 있다.
2. OpenAI tool calling을 단순 demo가 아니라 bounded backend workflow로 설계할 수 있다.
3. security, timeout, redaction, replay 같은 운영 제약을 코드와 테스트로 설명할 수 있다.
4. 다른 개발자가 따라 할 수 있도록 tutorial, article, build log로 콘텐츠화할 수 있다.

즉 StackSleuth는 "작동하는 코드"와 "설명 가능한 코드"를 동시에 보여주는 저장소다.

## 왜 챗봇이 아니라 backend investigation agent인가

가장 쉬운 AI 프로젝트는 채팅 UI를 만들고 모델 답변을 보여주는 것이다. 하지만 그런
프로젝트만으로는 backend engineer의 강점이 잘 드러나지 않는다.

StackSleuth는 문제를 다르게 잡았다.

- 사용자는 자연어로 운영 질문을 한다.
- 모델은 필요한 tool을 고른다.
- Spring은 허용된 tool만 실행한다.
- DB는 read-only 계정으로 한 번 더 제한한다.
- trace는 redaction된 상태로 저장된다.
- CLI는 현재 실행 과정을 terminal에서 보여주고, dashboard는 같은 trace를 더
  시각적으로 검토하게 만드는 역할을 맡는다.

이 구조는 backend 개발자가 잘하는 영역을 전면에 둔다. API boundary, data access,
transaction policy, audit log, test fixture, operational failure handling이 모두
project story의 일부가 된다.

## 왜 Spring, FastAPI, React로 나눴는가

StackSleuth의 구조는 기술을 많이 쓰기 위한 MSA가 아니다. 각 runtime이 가장 잘
하는 책임을 맡도록 나눈 것이다.

| Layer | Responsibility | Portfolio signal |
| --- | --- | --- |
| Spring Boot | 내부 tool 실행, 인증, SQL 정책, DB 권한 | Java backend depth |
| FastAPI | OpenAI Responses API loop, tool routing, trace persistence | agent orchestration |
| CLI | 빠른 developer workflow, replay command, safe terminal output | developer ergonomics |
| React dashboard | trace observability, replay visualization, human review | full-stack DX |
| Docs/articles | tutorial, rationale, failure cases, public explanation | developer education |

Spring에 OpenAI orchestration을 모두 넣을 수도 있었다. 하지만 frontier API와
agentic 기능은 Python SDK에서 먼저 따라가기 쉽고, OpenAI ecosystem 문서와 예제가
Python 중심인 경우가 많다. 반대로 실제 backend tool과 DB 권한은 Spring이 소유하는
편이 Java backend portfolio에 더 설득력 있다.

## 설계에서 의도적으로 드러낸 경계

StackSleuth는 "모델이 똑똑하다"보다 "시스템이 모델을 어떻게 다루는가"를 보여준다.

의도적으로 드러낸 경계는 다음과 같다.

- **Tool boundary:** 모델은 Spring endpoint를 직접 모른다. FastAPI가 허용된 tool만 route한다.
- **SQL boundary:** parser가 SELECT만 허용하고, PostgreSQL reader role이 실제 권한을 제한한다.
- **Loop boundary:** max iteration, request timeout, tool timeout, output token limit을 둔다.
- **Trace boundary:** replay는 재실행이 아니라 redacted persisted trace 조회다.
- **Output boundary:** CLI는 Spring internal endpoint를 직접 호출하지 않고, dashboard도 같은 원칙을 따른다.
- **Content boundary:** 구현된 것은 Draft, 아직 구현 전인 것은 Planned로 표시한다.

이 경계를 문서와 테스트에 남긴 이유는 면접관이나 오픈소스 독자가 저장소를 봤을 때
"데모가 우연히 돌아간다"가 아니라 "어디까지 안전하게 위임했는지 설명할 수 있다"를
확인할 수 있게 하기 위해서다.

## 각 PR이 보여주는 역량

StackSleuth는 기능 하나를 만들 때마다 지원용 증거도 함께 남기는 방식으로 쌓았다.

| Work | What it proves | Supporting article |
| --- | --- | --- |
| Spring Tool Server | AI agent용 내부 API를 안전하게 설계하는 능력 | [Article 01](01-safe-spring-tool-server.ko.md) |
| PostgreSQL demo and SQL safety | parser와 DB 권한을 함께 쓰는 defense-in-depth 사고 | [Article 02](02-defense-in-depth-sql-safety.ko.md) |
| FastAPI Agent Service | OpenAI Responses API loop와 tool calling boundary 이해 | [Article 03](03-openai-function-calling-agent-loop.ko.md) |
| Terminal CLI | 개발자가 실제로 쓰는 workflow와 replay semantics 설계 | [Article 04](04-terminal-cli-agent-trace-replay.ko.md) |
| Planned dashboard | agent output을 chat이 아니라 observability surface로 보는 관점 | [Article 05](05-react-agent-trace-dashboard.ko.md) |
| Planned evals | happy path보다 failure mode를 검증하려는 태도 | [Article 06](06-agent-failure-modes-and-evals.ko.md) |

이 표는 지원서에서 프로젝트를 설명할 때 유용하다. 단순히 "이런 기능을 만들었다"가
아니라, 각 작업이 어떤 DX 역량을 증명하는지 연결해주기 때문이다.

## 왜 문서가 코드만큼 중요한가

DX 직무에서는 구현 결과물만큼 그 결과물을 설명하는 방식이 중요하다. 좋은 샘플
프로젝트는 독자가 다음 질문에 빠르게 답할 수 있어야 한다.

- 이 프로젝트는 무엇을 보여주려는가?
- 지금 무엇이 구현됐고, 무엇은 planned인가?
- 로컬에서 어떻게 실행하는가?
- 실패하면 어디를 봐야 하는가?
- 왜 이런 architecture를 선택했는가?
- 이 코드를 다른 팀이 가져가면 어디를 바꿔야 하는가?

그래서 StackSleuth는 영어 문서와 한국어 원고를 역할별로 나눴다.

- `README.md`, `ARCHITECTURE.md`, `TUTORIAL.md`: global reviewer와 contributor를 위한 영어 문서
- `docs/articles/*.ko.md`: 한국어 본문 + 영어 요약으로 된 블로그 원고
- `docs/BUILD_LOG.md`: 시행착오와 수정 이유를 남기는 작업 기록
- `docs/SUBMISSION_CHECKLIST.md`: 지원 전 확인해야 할 evidence checklist

전부 bilingual로 만들지는 않았다. 모든 문서를 영어/한국어로 중복 관리하면 시간이
지날수록 내용이 어긋날 가능성이 크다. 대신 repository docs는 영어로 유지하고,
스토리텔링과 지원용 해설은 한국어 article로 남기는 구조를 선택했다.

## 현재 상태를 과장하지 않는 이유

포트폴리오 문서에서 가장 위험한 것은 미구현 기능을 완성된 것처럼 쓰는 것이다.
StackSleuth는 상태를 일부러 나눠 적는다.

- Spring Tool Server: implemented
- PostgreSQL demo data: implemented
- FastAPI Agent Service: implemented with mocked OpenAI/Spring verification
- Terminal CLI: implemented
- React dashboard: planned
- Failure-mode eval runner: planned
- Live OpenAI model quality eval: not claimed as automated evidence

이런 표현은 덜 화려해 보일 수 있다. 하지만 DX 역할에서는 신뢰가 더 중요하다.
문서가 구현 상태를 정확히 반영하면, reviewer는 이 프로젝트의 나머지 주장도 더
믿을 수 있다.

## 지원서에서 이렇게 설명할 수 있다

짧게 말하면:

```text
I built StackSleuth, a Spring Boot + FastAPI reference implementation showing
how an AI agent can safely investigate backend incidents through OpenAI tool
calling. The project focuses on bounded internal tools, read-only SQL safety,
trace replay, terminal developer workflow, and documentation that teaches the
architecture rather than hiding it behind a chatbot UI.
```

한국어로는 이렇게 설명할 수 있다.

```text
StackSleuth는 AI agent가 Spring Boot backend의 내부 도구를 안전하게 호출해 장애
원인을 조사하는 포트폴리오 프로젝트입니다. 단순 챗봇이 아니라 tool calling,
read-only SQL guardrail, timeout, redaction, trace replay, CLI workflow를 통해
AI에게 backend 작업을 어디까지 위임할 수 있는지 보여주는 reference implementation입니다.
```

면접에서 더 길게 설명해야 한다면 다음 흐름이 좋다.

1. Java/Spring backend 경험을 살리기 위해 내부 tool server를 Spring에 뒀다.
2. OpenAI orchestration은 FastAPI에서 명시적인 Responses API loop로 구현했다.
3. 모델이 선택해도 실행 권한은 Spring과 DB policy가 제한한다.
4. CLI는 현재 실행 결과와 판단 과정을 terminal에서 보여주고, dashboard는 같은 목적의 planned frontend다.
5. 각 단계마다 article, tutorial, build log를 남겨 DX 역량을 증명했다.

## 앞으로 보강할 증거

현재 남은 가장 큰 포트폴리오 보강점은 frontend와 demo asset이다.

- React trace dashboard 구현
- sample trace replay GIF
- guardrail rejection GIF
- failure-mode eval runner
- external blog publication URL
- README 상단의 strongest evidence 링크 정리

이 작업들이 추가되면 StackSleuth는 backend agent architecture뿐 아니라 full-stack
DX artifact로 더 설득력 있게 보일 것이다.

## 결론

StackSleuth는 "AI로 무언가 만들었다"보다 "AI 기능을 개발자가 믿고 사용할 수 있는
제품 경계로 바꿨다"를 보여주기 위한 프로젝트다.

OpenAI Developer Experience Engineer 지원에서 이 프로젝트가 말해주는 메시지는
단순하다.

```text
I can build the system, explain the system, and help other developers adopt it safely.
```
