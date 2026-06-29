# StackSleuth Web Dashboard

The dashboard is an agent observability and replay surface. It is intentionally
not a chatbot UI.

## Routes

- `/traces` shows the empty trace-selection state.
- `/traces/<traceId>` loads a persisted trace from the FastAPI Agent Service.
- `/replay` renders the bundled sample trace without an OpenAI API key.

## Local Development

```bash
npm ci
npm run dev
```

Open:

```text
http://localhost:5173/replay
```

To point trace detail pages at a different FastAPI service:

```bash
VITE_AGENT_API_BASE_URL=http://localhost:8000 npm run dev
```

## Verification

```bash
npm run lint
npm test
npm run build
npx playwright install chromium
npm run test:e2e
```

The dashboard calls only `GET /agent/traces/{traceId}` for persisted trace
pages. Replay mode uses bundled trace data and does not call OpenAI, Spring, or
FastAPI.
