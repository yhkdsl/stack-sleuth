# OpenAI Function Calling Agent Loop 구현하기

- **Publication status:** Draft based on Issue #3 implementation
- **Related implementation:** [Python FastAPI agent service](../../python-agent-service/README.md)
- **External URL:** Not published

**Tracking issue:** [Issue #3](https://github.com/yhkdsl/stack-sleuth/issues/3)
**Implementation PR:** [PR #11](https://github.com/yhkdsl/stack-sleuth/pull/11)

## English Summary

This article explains StackSleuth's explicit OpenAI Responses API loop. The
service uses strict function schemas, routes only approved calls to Spring
Boot, returns structured tool results to the model, and stops on independent
model-iteration, tool, and total-request limits. OpenAI response storage is
disabled; prior response items and encrypted reasoning content are carried
forward by the application. Sensitive tool output is redacted before model
continuation and checked again before local persistence. Traces can be replayed
without model or tool calls. Verification uses mocked OpenAI and Spring
boundaries plus an HTTP integration test. A live OpenAI run is intentionally
not claimed as automated evidence.

## 이 글의 대상과 목표

이 글은 Spring 백엔드에 LLM을 붙여 본 적은 있지만, 모델에게 내부 API 실행을
위임할 때 애플리케이션이 무엇을 책임해야 하는지 궁금한 개발자를 대상으로 한다.

완성된 구조에서 모델은 결정을 내리지만 실행 권한을 직접 갖지 않는다. Python
서비스는 허용된 도구와 실행 예산을 관리하고, Spring 서버는 인증·입력 검증·SQL
정책·DB 권한을 적용한다.

```text
User request
  -> POST /agent/run
  -> OpenAI Responses API
  -> strict function call
  -> Python tool router
  -> authenticated Spring tool endpoint
  -> structured function_call_output
  -> OpenAI Responses API
  -> redacted trace persistence
  -> final answer and trace ID
```

관련 코드는 [agent loop](../../python-agent-service/app/agent_loop.py),
[OpenAI adapter](../../python-agent-service/app/openai_client.py),
[Spring router](../../python-agent-service/app/tool_router.py)에서 확인할 수 있다.

## 왜 Agents SDK 대신 명시적인 loop를 작성했는가

이 프로젝트의 목표는 가장 짧은 코드가 아니라 agent 경계를 설명하는 것이다.
따라서 이번 MVP에서는 OpenAI Python SDK의 Responses API를 직접 사용했다.

명시적인 loop를 선택하면 다음 결정이 코드에 그대로 드러난다.

- 모델 호출 횟수는 최대 몇 번인가
- 동시에 몇 개의 도구를 실행할 수 있는가
- Spring timeout과 전체 요청 timeout은 어떻게 다른가
- 어떤 데이터를 다음 모델 입력으로 전달하는가
- 실패한 실행도 어떤 trace로 남기는가

프레임워크가 나쁘다는 뜻은 아니다. 제품 요구가 복잡해지면 Agents SDK의 tracing과
handoff가 유리할 수 있다. 다만 StackSleuth의 첫 구현에서는 실행 경계를 독자가
직접 읽고 테스트할 수 있는 편이 더 중요한 Developer Experience라고 판단했다.

## strict tool schema와 좁은 권한

모델에게는 `check_server_health`, `search_error_logs`,
`run_read_only_query` 세 도구만 제공한다. 각 schema는 `strict: true`,
필수 필드, `additionalProperties: false`, 숫자 범위를 포함한다.

```json
{
  "type": "function",
  "name": "search_error_logs",
  "strict": true,
  "parameters": {
    "type": "object",
    "properties": {
      "keyword": {"type": "string", "minLength": 1, "maxLength": 100},
      "sinceMinutes": {"type": "integer", "minimum": 1, "maximum": 1440},
      "limit": {"type": "integer", "minimum": 1, "maximum": 100}
    },
    "required": ["keyword", "sinceMinutes", "limit"],
    "additionalProperties": false
  }
}
```

schema는 모델 출력의 형태를 좁히지만 최종 보안 경계는 아니다. Python router는
등록되지 않은 도구를 `TOOL_NOT_ALLOWED`로 거부하고, Spring은 다시 인증과 정책을
검사한다. SQL은 Spring parser와 PostgreSQL read-only 계정 양쪽에서 제한된다.

## stateless Responses API loop

서비스는 OpenAI 응답 저장을 사용하지 않는다.

```python
response = await client.responses.create(
    model=model,
    input=input_items,
    include=["reasoning.encrypted_content"],
    tools=tool_schemas,
    parallel_tool_calls=False,
    max_tool_calls=1,
    store=False,
)
```

`store=false`라고 해서 상태가 사라지는 것은 아니다. 애플리케이션이 이전
`response.output`과 각 `function_call_output`을 다음 `input`에 다시 넣어야 한다.
reasoning model을 stateless하게 사용할 때는 encrypted reasoning item도 함께
보존한다. 이 방식은 OpenAI의
[conversation state guide](https://developers.openai.com/api/docs/guides/conversation-state)
와 [reasoning guide](https://developers.openai.com/api/docs/guides/reasoning)에 따른다.

StackSleuth는 병렬 호출을 끄고 응답당 도구 호출을 하나로 제한했다. 처리량보다
순서가 명확한 trace와 예측 가능한 실행 예산이 MVP에 더 중요하기 때문이다.

## 세 개의 독립적인 정지 장치

agent가 멈추지 않는 문제는 timeout 하나로 해결되지 않는다.

1. `AGENT_MAX_ITERATIONS`는 모델이 계속 도구를 선택하는 loop를 중단한다.
2. `TOOL_TIMEOUT_SECONDS`는 개별 Spring HTTP 요청을 제한한다.
3. `REQUEST_TIMEOUT_SECONDS`는 모델·도구 호출과 trace 저장을 포함한 전체 요청
   시간을 제한한다.
4. `MAX_USER_REQUEST_CHARS`는 모델 호출 전 사용자 입력 크기를 제한한다.
5. `MAX_OUTPUT_TOKENS`는 각 Responses API 출력 크기를 제한한다.

실행 예산 timeout은 `REQUEST_TIMEOUT`, 반복 소진은
`MAX_ITERATIONS_REACHED`, 개별 Spring timeout은 tool result의
`TOOL_TIMEOUT`으로 기록된다. 호출자는 HTTP 상태와 trace ID뿐 아니라
`persisted`를 함께 확인한다. `persisted=true`인 trace만 replay할 수 있다.

실행 실패와 저장 실패가 동시에 발생하면 원래 원인을 잃지 않는다. 예를 들어
`error.code`는 `REQUEST_TIMEOUT`을 유지하고, `persistenceError.code`는
`TRACE_PERSISTENCE_TIMEOUT`, `persisted`는 `false`가 된다. UI나 CLI는 이 경우
존재하지 않는 replay 링크를 만들면 안 된다.

| 실패 지점 | HTTP | 확인할 필드 |
| --- | ---: | --- |
| 모델 설정 없음 | 503 | `AGENT_NOT_CONFIGURED` |
| 입력 제한 초과 | 413 | `REQUEST_TOO_LARGE` |
| 실행 예산 소진 | 504 | `error`, `persisted` |
| 모델 incomplete | 409 | `MODEL_RESPONSE_INCOMPLETE` |
| 모델 failed | 502 | `MODEL_RESPONSE_FAILED`, 선택적 `providerCode` |
| 저장 deadline 초과 | 기존 상태 유지 | `persisted=false`, `persistenceError` |

Responses API가 `incomplete` 또는 `failed` 상태를 반환하면 빈 문자열을 성공
답변으로 처리하지 않는다. `max_output_tokens` 중단은
`MODEL_RESPONSE_INCOMPLETE`, 내용과 tool call이 모두 없는 완료 응답은
`EMPTY_MODEL_OUTPUT`으로 기록한다.

Spring의 `4xx`는 `rejected`, `5xx`와 연결 실패는 `failed`, timeout은
`timed_out`으로 구분한다. 정책 거부와 장애를 같은 실패로 표시하지 않는 이유는
운영자가 취할 행동이 다르기 때문이다.

## 모델 전달 전과 저장 전 redaction

trace에는 사용자 요청, 모델 답변, tool arguments와 results가 모두 들어간다.
Spring tool result는 다음 OpenAI 요청에 포함되기 전에 먼저 재귀적으로 검사한다.
따라서 로그나 DB 결과의 이메일·credential이 모델 입력으로 그대로 넘어가지
않는다. trace 저장 시에도 같은 검사를 다시 적용해 애플리케이션의 다른 경로에서
들어온 민감값을 방어적으로 제거한다.

- API key와 bearer-style credential 패턴
- password, credential, access token 같은 명시적 필드
- 이메일과 미국·한국 전화번호 패턴

초기 구현에서는 필드 이름에 `token`이 포함되면 전부 가렸다. 그 결과
`totalTokens`도 `[REDACTED]`가 되어 usage 관측이 깨졌다. 테스트가 이 문제를
발견했고, 현재는 정규화한 정확한 credential 필드 집합과 값 패턴을 분리한다.
이 시행착오는 [Build Log](../BUILD_LOG.md)에 남겼다.

로컬 파일 저장은 임시 파일을 만든 뒤 원자적으로 교체한다. 현재 방식은 MVP
replay에는 충분하지만 retention, 다중 프로세스 동시성, 외부 저장소 내구성을
제공하지 않는다.

`totalDurationMs`는 저장기의 첫 write pass가 끝난 뒤 확정되어 persisted JSON과
응답에 같은 값으로 남는다. 모델·도구 실행뿐 아니라 redaction, 직렬화, 주 저장
write 지연도 포함한다. 자기 자신의 최종 atomic replace 시간을 JSON 값에
재귀적으로 포함할 수는 없으므로 그 짧은 구간은 측정 범위에서 제외한다.

## API key 없이 검증하기

다음 예제는 실제 `AgentLoop`와 `FileTraceStore`를 사용하면서 OpenAI와 Spring만
scripted adapter로 교체한다.

```bash
cd python-agent-service
uv sync --locked --all-groups
uv run python ../examples/python-agent/mock_investigation.py
```

단위 테스트는 OpenAI SDK에 전달되는 strict tools, `store=false`, encrypted
reasoning include, tool-call continuation을 검증한다. Spring 호출은 mock HTTP로
endpoint, 내부 token, trace/request correlation header, timeout과 오류 분류를
검증한다. HTTP 통합 테스트는 다음 전체 경로를 통과한다.

```text
FastAPI -> AgentLoop -> mocked model -> SpringToolRouter
        -> mocked Spring HTTP -> redaction -> FileTraceStore -> replay API
```

현재 자동 검증은 live OpenAI 모델의 선택 품질을 평가하지 않는다. 그것은 고정된
eval dataset과 성공 기준을 추가하는 후속 작업의 범위다.

## 실행과 replay

실제 실행에서는 저장소 루트의 `.env.example`을 복사하고, 커밋되지 않는 `.env`에
`OPENAI_API_KEY`, `AGENT_MODEL`, `TOOL_SERVER_TOKEN`을 설정한다.

```bash
cd python-agent-service
uv run uvicorn app.main:app --reload --port 8000
```

```bash
curl -X POST http://localhost:8000/agent/run \
  -H 'Content-Type: application/json' \
  -d '{"request":"Investigate errors from the last hour and summarize the evidence."}'
```

```bash
curl http://localhost:8000/agent/traces/<trace_id>
```

API key가 없어도 서비스는 시작하고 저장된 trace를 replay할 수 있다. 이때 live
run은 secret을 요구하는 대신 `AGENT_NOT_CONFIGURED` 구조화 오류를 반환한다.

## 현재 제한사항

- live OpenAI 호출은 자동화된 검증 증거에 포함되지 않았다.
- 모델이 어떤 도구를 선택하는지에 대한 정량 eval은 아직 없다.
- trace 저장소는 로컬 단일 노드 MVP 구현이다.
- CLI와 React trace dashboard는 아직 구현되지 않았다.
- 비용은 검증된 pricing metadata가 없으므로 추정하지 않는다.

이 제한을 명시하는 이유는 포트폴리오에서 “작동하는 코드”와 “계획된 제품”을
구분하기 위해서다. 다음 단계는 trace dashboard가 같은 redacted 계약을 읽도록
만들고, 성공·거부·timeout 시나리오를 replay fixture로 고정하는 것이다.
