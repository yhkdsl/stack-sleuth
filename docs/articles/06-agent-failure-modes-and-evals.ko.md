# AI Agent의 timeout, 무한 반복, 개인정보 문제 검증하기

- **Publication status:** Draft based on Issue #6 implementation and local verification
- **Related implementation:** `evals/scenarios.yml`, `evals/run_evals.py`, and eval runner tests
- **External URL:** Not published

**Tracking issue:** [Issue #6](https://github.com/yhkdsl/stack-sleuth/issues/6)

## English Summary

This article explains how StackSleuth evaluates failure-oriented behavior for an AI agent. It demonstrates a successful incident investigation, destructive SQL rejection, tool timeout handling, and max-iteration stopping with deterministic scenarios that do not require an OpenAI API key or a running Spring server.

## 왜 happy path만으로는 부족한가

에이전트 데모는 정상적인 tool call 두 번만 보여주면 쉽게 완성된 것처럼 보인다. 실제 신뢰성은 모델이 반복을 멈추지 않거나, 도구가 응답하지 않거나, trace에 민감정보가 섞일 때 드러난다.

구현된 eval scenario:

- null profile incident 정상 조사
- destructive SQL rejection
- tool timeout
- max iteration stop

이 eval은 live model quality benchmark가 아니다. 모델이 실제로 어떤 tool을 선택하는지 평가하려면 별도의 dataset과 judge가 필요하다. 여기서는 MVP의 안전 contract를 반복 가능한 fixture로 검증하는 데 집중한다.

## 구현 방식

`evals/scenarios.yml`은 JSON-compatible YAML 형태의 deterministic scenario 파일이다. 외부 YAML parser를 추가하지 않기 위해 표준 라이브러리 `json`으로 읽을 수 있는 형식을 사용했다. 각 scenario는 다음을 가진다.

- user request
- scripted model turns
- scripted tool results
- expected tool calls
- expected guardrail/error codes
- final answer에 포함되어야 하는 evidence

runner는 production `AgentLoop`와 `FileTraceStore`를 그대로 사용한다. 다른 점은 OpenAI client와 Spring router 대신 scripted adapter를 주입한다는 것이다. 이 덕분에 CI에서 API key 없이도 agent trace contract를 검증할 수 있다.

```bash
cd python-agent-service
uv run python ../evals/run_evals.py
```

예상 출력:

```text
PASS null_profile_image_incident trace=eval_null_profile_image_incident
PASS destructive_sql_rejection trace=eval_destructive_sql_rejection
PASS tool_timeout trace=eval_tool_timeout
PASS max_iteration_stop trace=eval_max_iteration_stop
```

## 검증한 실패 모드

### Destructive SQL rejection

모델이 `DELETE FROM users WHERE id = 42`를 실행하려는 turn을 만들면, scripted tool result는 `rejected` 상태와 `SQL_WRITE_BLOCKED` error code를 반환한다. runner는 이 code가 `guardrailRejections`에 남았는지 검증한다.

### Tool timeout

tool result가 `timed_out`과 `TOOL_TIMEOUT`을 반환하는 scenario를 둔다. 이 scenario는 max iteration budget을 1로 제한해 incomplete trace를 만든다. runner는 trace ID가 남고, tool result에 timeout code가 보존되는지 확인한다.

### Max iteration stop

모델이 final answer 없이 계속 `check_server_health` tool call만 내는 scenario를 둔다. `maxIterations=2` 이후 trace는 `incomplete`가 되고 `MAX_ITERATIONS_REACHED`를 기록해야 한다.

## 왜 이 방식이 DX에 중요한가

DX 포트폴리오에서 중요한 것은 "데모가 한 번 잘 됐다"가 아니다. 사용자가 프로젝트를 clone했을 때, 실패 상황까지 재현 가능한 명령으로 확인할 수 있어야 한다. 이 runner는 다음 신호를 만든다.

- API key 없이도 reviewer가 안전 contract를 확인할 수 있다.
- happy path와 failure path가 같은 trace model로 검증된다.
- guardrail rejection, timeout, max iteration이 README 문장만이 아니라 executable evidence로 남는다.
- dashboard와 CLI가 표시해야 하는 상태들이 fixture로 고정된다.

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

## 발행 체크리스트

완료:

- eval runner가 로컬에서 실행됨
- Python CI에 eval runner 실행 단계 추가
- 각 failure scenario의 기대 상태와 trace event가 assertion으로 검증됨
- eval fixture에 실제 개인정보, credential, token 없음

남은 작업:

- 외부 블로그 발행
- README에 sanitized GIF/screenshot을 추가할 때 eval 결과 표 함께 포함
