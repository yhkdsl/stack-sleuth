# Agent의 판단 과정을 React로 시각화하기

- **Publication status:** Planned until Issue #5 is implemented and visually verified
- **Related implementation:** React trace and replay dashboard
- **External URL:** Not published

**Tracking issue:** [Issue #5](https://github.com/yhkdsl/stack-sleuth/issues/5)

## English Summary

This planned article will show why StackSleuth uses an observability dashboard instead of a chat interface. It will cover trace timelines, evidence rendering, guardrail and failure states, redaction labels, replay without an API key, and the human review applied to AI-assisted frontend development.

## 핵심 질문

최종 답변만 보여주는 UI에서는 모델이 어떤 도구를 왜 호출했고 어떤 근거를 사용했는지 확인하기 어렵다. StackSleuth dashboard는 대화 UI보다 실행 trace를 우선한다.

예정된 화면 요소:

- original request와 final answer
- ordered tool timeline
- tool input과 redacted output
- `rejected`와 `failed`의 분리 표시
- evidence table
- latency와 token usage
- sample trace replay

## AI로 프론트엔드를 만들었다는 설명 방식

AI-assisted frontend development를 단순한 코드 생성으로 설명하지 않는다. 원고에는 다음 인간 검토 과정을 포함한다.

- 도메인에 맞는 정보 구조 선택
- loading, empty, error, partial 상태 검토
- 긴 SQL과 JSON의 responsive behavior 확인
- 접근 가능한 색상 외 상태 표시
- Playwright desktop/mobile screenshot 검증

## 발행 조건

- 실제 dashboard 구현과 component tests 통과
- Playwright smoke test 통과
- desktop/mobile 시각 검증
- sample replay가 OpenAI API key 없이 동작
- sanitized screenshot 또는 GIF 포함
