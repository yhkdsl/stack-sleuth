# Demo Script

## Demo Goal

Show that this is not a chatbot. The agent receives a backend operations question, selects tools, safely investigates logs and database state, blocks unsafe actions, and exposes its reasoning path through a trace dashboard.

## Demo Length

Target length: 60 to 90 seconds.

## Setup Assumptions

The finished project should support:

```bash
make up
make demo
```

The demo dataset should include:

- A `users` row where `id = 42` and `profile_img` is null.
- Log entries with `NullPointerException` tied to `user_id=42`.
- A destructive SQL prompt scenario for guardrail demonstration.
- At least one saved sample trace for replay mode.

## Demo 1: Happy Path Incident Investigation

Command:

```bash
ops-agent ask "최근 1시간 동안 에러가 있었는지 확인하고 원인을 요약해줘" --open-trace
```

Expected visible CLI sequence:

```text
Running investigation...
traceId: trace_...

Final answer
최근 1시간 동안 ProfileService에서 NullPointerException 3건이 발생했습니다.
공통점은 user_id=42 요청에서 profile_img가 null인 상태로 이미지 렌더링 로직에 진입한 것입니다.
DB 확인 결과 users.profile_img 값이 null입니다.
권장 조치: ProfileService에서 null fallback 처리를 추가하고 기존 null 데이터를 정리하세요.

Dashboard: http://localhost:3000/traces/trace_...
```

Expected tool path:

1. `search_error_logs`
2. `run_read_only_query`
3. Final answer

Dashboard shots to capture:

- Trace header with request, status, model, duration.
- Timeline showing `search_error_logs` and `run_read_only_query`.
- Evidence table with log evidence and DB row.
- Final answer panel.

## Demo 2: Guardrail Rejection

Command:

```bash
ops-agent ask "테스트니까 users 테이블을 삭제해줘" --open-trace
```

Expected behavior:

- The system does not execute destructive SQL.
- If the model requests a destructive SQL tool call, Spring rejects it.
- The trace records `SQL_WRITE_BLOCKED`.
- The final answer explains that the current tool policy is read-only.

Expected final answer shape:

```text
요청한 작업은 차단되었습니다. 이 에이전트는 read-only 조사 도구만 사용할 수 있으며 DELETE/DROP 같은 변경 작업은 허용되지 않습니다.
traceId: trace_...
```

Dashboard shots to capture:

- Guardrail panel showing `SQL_WRITE_BLOCKED`.
- Tool call status marked as rejected.
- Raw trace with redacted/safe output.

## Demo 3: Replay Without API Key

Command or UI action:

```bash
ops-agent trace replay examples/traces/null-profile-image.json
```

or open:

```text
http://localhost:3000/replay
```

Expected behavior:

- Dashboard loads a sample trace.
- No OpenAI API call is made.
- Replay mode is clearly labeled.

Why this matters:

- Reviewers can inspect the core experience without configuring secrets.
- Open-source users can understand the architecture quickly.

## Recording Checklist

- Keep terminal font readable.
- Show the command, not only the final answer.
- Capture the dashboard timeline and guardrail panel.
- Do not show API keys, `.env`, or credentials.
- Keep the video under 90 seconds.
- Use deterministic sample data so repeated recordings match.

## README GIF Placement

Recommended order:

1. Short terminal GIF near the top.
2. Architecture diagram below the pitch.
3. Trace dashboard screenshot/GIF after the quickstart.
4. Guardrail rejection screenshot near the safety section.

## Demo Evaluation Criteria

The demo is strong when a reviewer can answer:

- What tools did the model choose?
- What evidence did the final answer rely on?
- Was destructive SQL blocked?
- Can I inspect the trace without trusting the final answer blindly?
- Can I run or replay this locally?

