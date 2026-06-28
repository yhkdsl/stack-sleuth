# AI Agent의 timeout, 무한 반복, 개인정보 문제 검증하기

- **Publication status:** Planned until Issue #6 is implemented and verified
- **Related implementation:** Agent evals, redaction, and failure-mode tests
- **External URL:** Not published

**Tracking issue:** [Issue #6](https://github.com/yhkdsl/stack-sleuth/issues/6)

## English Summary

This planned article will focus on failure-oriented evaluation for an AI agent. It will demonstrate bounded iterations, tool and request timeouts, destructive SQL rejection, incomplete-investigation responses, and trace redaction. The goal is to show repeatable evidence that the system fails safely instead of presenting only a successful demo.

## 왜 happy path만으로는 부족한가

에이전트 데모는 정상적인 tool call 두 번만 보여주면 쉽게 완성된 것처럼 보인다. 실제 신뢰성은 모델이 반복을 멈추지 않거나, 도구가 응답하지 않거나, trace에 민감정보가 섞일 때 드러난다.

예정된 eval scenario:

- null profile incident 정상 조사
- destructive SQL rejection
- tool timeout
- max iteration stop
- API key, access token, DB credential, 이메일 redaction

## 결과 표현 원칙

실패한 조사를 억지로 성공 답변으로 꾸미지 않는다. 최종 응답은 완료 여부, 수집된 근거, 실패 지점, trace ID를 명확히 구분한다.

```json
{
  "status": "incomplete",
  "reason": "TOOL_TIMEOUT",
  "traceId": "trace_example",
  "evidence": []
}
```

## 발행 조건

- eval runner가 로컬과 CI에서 실행됨
- 각 failure scenario의 기대 상태와 trace event가 assertion으로 검증됨
- redaction fixture에 실제 개인정보가 없음
- dashboard에서 incomplete, rejected, failed 상태가 구분됨
- 결과 표와 재현 명령 포함
