# Demo Script

## Demo Goal

Show that this is not a chatbot. The agent receives a backend operations question, selects tools, safely investigates logs and database state, blocks unsafe actions, and exposes its reasoning path through a trace dashboard.

## Demo Length

Target length: 60 to 90 seconds.

## Setup Assumptions

The current MVP uses explicit commands instead of a Makefile:

```bash
cp .env.example .env
docker compose --env-file .env -f infra/docker-compose.yml up -d --wait
./gradlew :spring-tool-server:bootRun
cd python-agent-service
uv run uvicorn app.main:app --reload --port 8000
cd ../web-dashboard
npm run dev
```

The demo dataset should include:

- A `users` row where `id = 42` and `profile_img` is null.
- Log entries with `NullPointerException` tied to `user_id=42`.
- A destructive SQL prompt scenario for guardrail demonstration.
- At least one saved sample trace for replay mode.

## Demo 1: Happy Path Incident Investigation

Command:

```bash
cd python-agent-service
uv run ops-agent ask "Investigate errors from the last hour and summarize the cause." --open-trace
```

Expected visible CLI sequence:

```text
Final answer
Three recent errors point to a NullPointerException in ProfileService.
The evidence suggests user 42 has a null profile_img value.

Trace: trace_...
Status: completed

Evidence
- search_error_logs: success
- run_read_only_query: success

Dashboard: http://localhost:5173/traces/trace_...
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
cd python-agent-service
uv run ops-agent ask "Show whether destructive SQL is blocked by the local read-only policy." --open-trace
```

Expected behavior:

- The system does not execute destructive SQL.
- If the model requests a destructive SQL tool call, Spring rejects it.
- The trace records `SQL_WRITE_BLOCKED`.
- The final answer explains that the current tool policy is read-only.

Expected final answer shape:

```text
Final answer
The destructive SQL request was rejected. StackSleuth only allows read-only
investigation tools, and the Spring SQL guardrail returned SQL_WRITE_BLOCKED
before any write was executed.

Trace: trace_...
Status: completed
```

Dashboard shots to capture:

- Guardrail panel showing `SQL_WRITE_BLOCKED`.
- Tool call status marked as rejected.
- Raw trace with redacted/safe output.

## Demo 3: Replay Without API Key

UI action:

```text
http://localhost:5173/replay
```

For CLI replay of a persisted run, use the trace ID returned by the agent
service:

```bash
cd python-agent-service
uv run ops-agent trace replay trace_...
```

Expected behavior:

- Dashboard loads a sample trace.
- No OpenAI API call is made.
- Replay mode is clearly labeled.

Why this matters:

- Reviewers can inspect the core experience without configuring secrets.
- Open-source users can understand the architecture quickly.

## Recording Checklist

- Prefer the sanitized checked-in frames under `docs/assets/` for README until
  a clean manual recording is available.
- Keep terminal font readable.
- Show the command, not only the final answer.
- Capture the dashboard timeline and guardrail panel.
- Do not show API keys, `.env`, or credentials.
- Do not show shell history, local account names, browser profile menus, or
  unrelated desktop applications.
- Keep the video under 90 seconds.
- Use deterministic sample data so repeated recordings match.
- Use the sample replay page (`http://localhost:5173/replay`) when recording
  without an OpenAI API key.

## README GIF Placement

Recommended order:

1. Short terminal GIF or sanitized static terminal frame near the top.
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
