# OpenAI Function Calling Agent Loop 구현하기

**Publication status:** Planned until Issue #3 is implemented and verified  
**Related implementation:** Python FastAPI agent service  
**External URL:** Not published

**Tracking issue:** [Issue #3](https://github.com/yhkdsl/stack-sleuth/issues/3)

## English Summary

This planned article will explain the verified StackSleuth agent loop: how the OpenAI Responses API selects strict tools, how tool calls are routed to Spring Boot, how results return to the model, and how iteration, tool, and total-request limits stop runaway execution. The article will not be published as an implementation guide until the service and mocked tests exist.

## 독자가 얻게 될 것

- Responses API의 tool call과 tool result 흐름
- Spring 내부 API를 모델에게 직접 노출하지 않는 tool router
- 최대 반복 횟수와 timeout을 상태 머신에 포함하는 방법
- 모델 응답, 도구 결과, 최종 답변을 하나의 redacted trace로 저장하는 방법

## 예정된 흐름

```text
User request
  -> FastAPI agent run
  -> OpenAI response
  -> validated tool call
  -> Spring tool server
  -> structured tool result
  -> OpenAI response
  -> final answer and persisted trace
```

글에는 `POST /agent/run`, strict tool schema, mocked OpenAI response, timeout 실패 예제를 포함한다. 실제 코드와 테스트가 완성되기 전에는 상세 구현 예제를 추가하지 않는다.

## 발행 조건

- Issue #3 acceptance criteria 통과
- max iteration, tool timeout, total timeout 테스트 통과
- trace redaction 테스트 통과
- OpenAI SDK 사용 방식이 공식 문서와 일치하는지 재검토
- API key 없이 실행 가능한 mocked example 제공
