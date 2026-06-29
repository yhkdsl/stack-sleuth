# Agent의 판단 과정을 React로 시각화하기

- **Publication status:** Draft based on Issue #5 implementation and visual verification
- **Related implementation:** `web-dashboard` React trace and replay dashboard
- **External URL:** Not published

**Tracking issue:** [Issue #5](https://github.com/yhkdsl/stack-sleuth/issues/5)

## English Summary

This article explains why StackSleuth uses an observability dashboard instead of a chat interface. It covers trace timelines, evidence rendering, guardrail and failure states, redaction labels, replay without an API key, and the human review applied to AI-assisted frontend development.

## 핵심 질문

최종 답변만 보여주는 UI에서는 모델이 어떤 도구를 왜 호출했고 어떤 근거를 사용했는지 확인하기 어렵다. StackSleuth dashboard는 대화 UI보다 실행 trace를 우선한다.

구현된 화면 요소:

- original request와 final answer
- ordered tool timeline
- tool input과 redacted output
- `rejected`와 `failed`의 분리 표시
- evidence table
- latency와 token usage
- sample trace replay

## 왜 chatbot UI가 아닌가

이 프로젝트의 사용자 경험은 "질문을 입력하고 답변을 받는다"에서 끝나면 안 된다.
Developer Experience Engineer 관점에서 더 중요한 질문은 다음과 같다.

- 모델이 어떤 tool을 선택했는가?
- tool input과 output은 안전한가?
- guardrail rejection은 성공/실패와 구분되는가?
- final answer가 어떤 evidence에 기대고 있는가?
- API key 없이도 reviewer가 핵심 흐름을 볼 수 있는가?

그래서 dashboard는 message bubble을 중심에 두지 않는다. 대신 trace header,
ordered tool timeline, guardrail review, evidence table, runtime metrics, raw trace
viewer를 배치했다. 이 구조는 "agent가 답했다"보다 "agent가 어떻게 조사했는지
검토할 수 있다"를 보여준다.

## 구현한 경계

`web-dashboard`는 Spring internal endpoint를 호출하지 않는다. persisted trace page는
FastAPI Agent Service의 `GET /agent/traces/{traceId}`만 호출한다. `/replay`는 bundled
sample trace를 렌더링하므로 OpenAI API key, Spring server, FastAPI server가 없어도
동작한다.

이 결정은 의도적으로 보수적이다. Dashboard가 Spring tool endpoint를 직접 호출하면
frontend가 또 하나의 tool executor가 된다. StackSleuth에서 실행 권한은 Spring과
FastAPI 경계 안에 남겨두고, frontend는 이미 redaction된 trace를 읽는 관찰 표면으로
제한했다.

## 구현과 검증

구현 범위:

- Vite + React + TypeScript dashboard
- `/traces`, `/traces/<traceId>`, `/replay` route
- `TraceHeader`, `TraceTimeline`, `ToolCallCard`, `GuardrailPanel`,
  `EvidenceTable`, `CostLatencyPanel`, `FinalAnswerPanel`, `RawTraceViewer`,
  `EmptyState`, `ErrorState`
- checked-in sample trace: `examples/traces/null-profile-image.json`
- component tests and Playwright replay smoke test

검증 명령:

```bash
cd web-dashboard
npm run lint
npm test
npm run build
npm run test:e2e
```

추가로 desktop/mobile screenshot을 확인해 긴 trace ID, tool name, SQL/JSON block,
mobile stacking에서 텍스트가 겹치지 않는지 검토했다.

## AI로 프론트엔드를 만들었다는 설명 방식

AI-assisted frontend development를 단순한 코드 생성으로 설명하지 않는다. 원고에는 다음 인간 검토 과정을 포함한다.

- 도메인에 맞는 정보 구조 선택
- loading, empty, error, partial 상태 검토
- 긴 SQL과 JSON의 responsive behavior 확인
- 접근 가능한 색상 외 상태 표시
- Playwright desktop/mobile screenshot 검증

## Developer Experience Engineer 지원 포인트

이 대시보드는 "프론트엔드도 만들 수 있다"를 보여주기 위한 장식이 아니다. DX 직무 관점에서 더 중요한 신호는 개발자가 agentic system을 신뢰하고 디버깅할 수 있도록 제품 표면을 설계했다는 점이다.

지원서나 면접에서는 다음처럼 설명할 수 있다.

- CLI는 빠른 실행 표면이고, dashboard는 실행 후 검토 표면이다.
- OpenAI나 Spring tool server를 직접 다시 호출하지 않는 replay mode를 제공해 reviewer가 API key 없이도 핵심 흐름을 확인할 수 있게 했다.
- tool call, guardrail rejection, redaction, latency, token usage를 한 화면에서 보여줘 agent의 답변을 검증 가능한 evidence로 바꿨다.
- AI-assisted frontend generation을 사용했지만, 최종 품질은 component boundary, error state, responsive layout, test, screenshot review로 검증했다.

즉 이 PR의 핵심 어필 포인트는 "React 화면을 붙였다"가 아니라 "AI agent의 판단 과정을 사람이 이해하고 재현할 수 있는 developer experience로 번역했다"이다.

## 발행 체크리스트

완료:

- 실제 dashboard 구현과 component tests 통과
- Playwright smoke test 통과
- desktop/mobile 시각 검증
- sample replay가 OpenAI API key 없이 동작

발행 전 남은 작업:

- sanitized screenshot 또는 GIF를 README와 외부 블로그 글에 포함
