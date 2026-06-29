# AI Agent의 실행 과정을 터미널 CLI로 안전하게 보여주는 방법

- **Publication status:** Draft based on Issue #4 implementation
- **Related implementation:** [Terminal CLI](../../python-agent-service/ops_agent)
- **External URL:** Not published

**Tracking issue:** [Issue #4](https://github.com/yhkdsl/stack-sleuth/issues/4)
**Implementation PR:** [PR #12](https://github.com/yhkdsl/stack-sleuth/pull/12)

## English Summary

This article explains why StackSleuth's `ops-agent` CLI is intentionally a thin
client over the FastAPI agent service. The CLI starts investigations, prints the
final answer first, exposes compact evidence, expands redacted tool results in
verbose mode, and replays persisted traces without calling OpenAI or Spring.
It does not call internal Spring tool endpoints directly. That boundary keeps
model orchestration, tool execution, trace persistence, and redaction in the
backend while giving developers a fast terminal workflow. The implementation
also handles non-persisted traces, malformed API errors, connection failures,
and invalid timeout configuration without leaking secrets or showing Python
tracebacks.

## 이 글의 대상과 목표

이 글은 AI agent를 만들 때 "터미널에서 자연어로 실행하면 멋있다"에서 한 단계 더
나아가, 그 터미널 UX가 어떤 보안 경계와 관측 가능성을 지켜야 하는지 궁금한
개발자를 대상으로 한다.

StackSleuth의 CLI 목표는 shell에서 agent 조사를 시작하는 것이다. 하지만 CLI가
Spring 내부 tool endpoint를 직접 호출하면 구조가 흐려진다. 그러면 terminal
client가 또 하나의 executor가 되고, FastAPI agent service가 가진 trace,
redaction, timeout, replay 책임이 분산된다.

따라서 `ops-agent`는 일부러 얇게 만들었다.

```text
ops-agent ask
  -> POST /agent/run
  -> FastAPI Agent Service
  -> OpenAI Responses API
  -> Spring Tool Server
  -> redacted trace
  -> terminal answer and evidence

ops-agent trace replay
  -> GET /agent/traces/{traceId}
  -> persisted redacted trace only
```

관련 코드는 [CLI main](../../python-agent-service/ops_agent/main.py),
[CLI client](../../python-agent-service/ops_agent/client.py),
[CLI formatting](../../python-agent-service/ops_agent/formatting.py)에서 확인할 수 있다.

## 왜 CLI가 Spring tool endpoint를 직접 호출하지 않는가

처음 보기에는 CLI가 `check_server_health`, `search_error_logs`,
`run_read_only_query`를 직접 호출하는 편이 단순해 보인다. 하지만 이 방식은
agent의 핵심 경계를 깨뜨린다.

Spring Tool Server는 내부 도구의 실행 정책을 책임진다. FastAPI Agent Service는
모델 호출, tool 선택, 반복 제한, 전체 timeout, tool 결과 redaction, trace 저장을
책임진다. CLI가 Spring을 직접 호출하면 다음 문제가 생긴다.

- 모델이 왜 그 도구를 선택했는지 trace가 남지 않는다.
- CLI와 FastAPI 양쪽에 tool 호출 로직이 중복된다.
- replay가 실제 재실행인지 저장된 trace 조회인지 불명확해진다.
- terminal output redaction이 backend redaction과 어긋날 수 있다.
- dashboard와 CLI가 서로 다른 데이터 계약을 사용하게 된다.

그래서 CLI는 두 API만 사용한다.

```text
POST /agent/run
GET /agent/traces/{traceId}
```

이 결정은 코드도 단순하게 만든다. CLI는 "조사 실행과 trace 표시"만 알고, 어떤
Spring 도구가 존재하는지는 알 필요가 없다.

## 기본 실행 UX

FastAPI service가 실행 중이면 다음처럼 조사를 시작한다.

```bash
cd python-agent-service
uv run ops-agent ask "Investigate errors from the last hour and summarize the evidence."
```

출력은 최종 답변을 먼저 보여준다. 사용자가 가장 궁금한 것은 "그래서 무슨 일이
있었나"이기 때문이다. 그 다음 trace ID와 compact evidence를 보여준다.

```text
Final answer
Three errors were found in the last hour.

Trace: trace_cli_123
Status: completed
Duration: 1000 ms

Evidence
- search_error_logs: success (12 ms)
```

이 순서는 dashboard가 없어도 terminal만으로 데모가 가능한 흐름을 만든다. 동시에
trace ID를 함께 보여주므로 나중에 같은 조사를 다시 열어볼 수 있다.

## verbose는 디버깅 모드이지 다른 실행 모드가 아니다

`--verbose`는 agent를 다르게 실행하지 않는다. 같은 `POST /agent/run` 결과를 더
자세히 렌더링할 뿐이다.

```bash
uv run ops-agent ask "Investigate errors from the last hour" --verbose
```

verbose 출력에는 다음 정보가 포함된다.

- ordered tool calls
- redacted tool result payloads
- guardrail rejections
- redaction events
- total token usage

tool result payload는 보기 편하게 JSON으로 출력하되, terminal이 긴 로그나 query
결과로 무너지는 것을 막기 위해 길이를 제한한다. 더 중요한 점은 출력 직전에
redaction을 다시 적용한다는 것이다. trace 저장 단계에서 이미 redaction이
일어나지만, CLI는 terminal이라는 별도 노출 경계를 갖기 때문에 방어적으로 한 번 더
검사한다.

## replay는 재실행이 아니다

운영 도구에서 replay라는 단어는 조심해서 써야 한다. 어떤 시스템에서는 replay가
실제 side effect를 다시 발생시킬 수 있기 때문이다.

StackSleuth의 `trace replay`는 저장된 trace를 다시 표시하는 기능이다.

```bash
uv run ops-agent trace replay trace_cli_123
```

이 명령은 `GET /agent/traces/{traceId}`만 호출한다. OpenAI도 호출하지 않고,
Spring Tool Server도 호출하지 않는다. 따라서 API key가 없어도 저장된 trace를
검토할 수 있고, read-only 조사라도 불필요한 DB query를 다시 실행하지 않는다.

`trace show`와 `trace replay`의 차이는 의도 표현이다. 둘 다 같은 API를 읽지만,
`replay`는 사용자가 "저장된 실행 기록을 다시 보는 중"이라는 맥락을 terminal에
표시한다.

## persisted=false일 때 링크를 만들지 않는다

Issue #3에서 trace 저장 실패와 실행 실패가 동시에 발생하는 경우를 다뤘다. 이때
응답에는 `traceId`가 있을 수 있지만, `persisted=false`라면 실제 replay endpoint가
그 trace를 찾지 못할 수 있다.

그래서 `--open-trace`는 `traceId`만 보고 dashboard URL을 만들지 않는다.

```bash
uv run ops-agent ask "Investigate errors from the last hour" --open-trace
```

`persisted=true`일 때만 다음처럼 URL을 출력한다.

```text
Dashboard: http://localhost:5173/traces/trace_cli_123
```

저장되지 않은 trace라면 링크 대신 이유를 보여준다.

```text
Trace replay unavailable: TRACE_PERSISTENCE_TIMEOUT
```

작은 차이처럼 보이지만 Developer Experience에서는 중요하다. 깨진 링크를 보여주는
CLI는 사용자를 잘못된 다음 행동으로 이끈다.

## 실패 출력은 구조화하되 traceback은 숨긴다

CLI 사용자는 Python 내부 stack trace보다 "내가 무엇을 고쳐야 하는지"를 원한다.
예를 들어 OpenAI 설정이 없으면 FastAPI는 구조화된 오류를 반환한다.

```json
{
  "code": "AGENT_NOT_CONFIGURED",
  "message": "Set OPENAI_API_KEY and AGENT_MODEL to enable live agent runs."
}
```

CLI는 이 메시지를 그대로 echo하지 않는다. 환경변수 이름과 credential 관련 표현은
terminal 출력 전에 안전한 표현으로 바꾼다.

```text
AGENT_NOT_CONFIGURED: Set agent credentials and agent model to enable live agent runs.
```

또한 proxy나 upstream이 예상과 다른 shape를 반환해도 traceback으로 죽지 않는다.

```json
{"error": "upstream failed"}
```

이 경우 CLI는 fallback code로 출력한다.

```text
AGENT_REQUEST_FAILED: upstream failed
```

잘못된 timeout 환경변수도 마찬가지다.

```bash
STACKSLEUTH_AGENT_TIMEOUT_SECONDS=not-a-number \
  uv run ops-agent ask "Investigate errors"
```

이 값 때문에 Python traceback을 보여주지 않고 기본 timeout으로 돌아간다. 설정
실수를 terminal UX가 증폭시키지 않게 하는 선택이다.

## 테스트로 고정한 CLI 계약

CLI 테스트는 FastAPI 호출을 전부 mock한다. live OpenAI나 Spring에 의존하지 않고
terminal 계약을 검증하기 위해서다.

검증한 항목은 다음과 같다.

- happy path에서 final answer가 trace보다 먼저 출력된다.
- `ask`는 `POST /agent/run`만 호출한다.
- `trace show`와 `trace replay`는 `GET /agent/traces/{traceId}`만 호출한다.
- replay는 `/agent/run`을 호출하지 않는다.
- `--verbose`는 tool calls, tool results, guardrail rejections, redactions,
  token usage를 출력한다.
- `--open-trace`는 persisted trace에만 dashboard URL을 출력한다.
- API error와 connection error는 구조화된 안전 메시지를 출력한다.
- terminal 출력에는 이메일, 전화번호, credential-shaped value가 남지 않는다.

검증 명령은 다음과 같다.

```bash
cd python-agent-service
uv run pytest -q tests/test_cli.py
uv run pytest -q --cov=app --cov=ops_agent --cov-report=term-missing --cov-fail-under=90
uv run ruff check . ../examples/python-agent/mock_investigation.py
```

PR #12 기준으로 CLI 관련 보정 후 전체 Python 테스트는 51개가 통과했고 coverage는
96% 이상이었다. Spring Tool Server 회귀 테스트와 fixture 민감정보 검사도 함께
확인했다.

## 이 구현에서 배운 DX 원칙

좋은 CLI는 기능을 많이 넣은 CLI가 아니라 다음 행동을 헷갈리지 않게 만드는
CLI다. StackSleuth에서 그 원칙은 다음 결정으로 나타났다.

- 내부 tool endpoint를 숨기고 agent API만 노출한다.
- 최종 답변을 먼저 보여주되, evidence와 trace ID를 함께 제공한다.
- verbose는 더 자세한 표시일 뿐 다른 실행 경로가 아니다.
- replay는 재실행이 아니라 persisted trace 조회다.
- persisted되지 않은 trace에는 dashboard link를 만들지 않는다.
- terminal 출력은 저장 trace와 별도로 다시 redaction한다.
- 오류는 구조화하되 Python traceback과 raw credential 표현은 숨긴다.

이런 선택은 데모의 화려함보다 운영자의 신뢰를 우선한다. Developer Experience
Engineer가 만드는 도구라면 "어떻게 쓰는가"만큼 "어디까지 믿어도 되는가"를
명확하게 보여줘야 한다.

## 현재 제한사항

- React dashboard는 아직 구현되지 않았다. `--open-trace`는 URL을 출력하지만 실제
  화면은 후속 Issue #5 범위다.
- CLI는 local developer workflow를 목표로 하며, standalone binary packaging이나
  shell completion은 아직 없다.
- live OpenAI 모델이 어떤 tool path를 선택하는지에 대한 품질 평가는 별도 eval
  작업이 필요하다.
- terminal payload rendering은 bounded JSON 출력 수준이다. 큰 table이나 diff를
  사람이 더 읽기 좋게 렌더링하는 작업은 dashboard에서 다루는 편이 낫다.
