# Frontend Dashboard Plan

## 1. Positioning

The frontend is not a chatbot. It is an agent observability and replay dashboard.

The main interaction remains developer-native:

```bash
ops-agent ask "최근 1시간 에러 분석해줘" --open-trace
```

The dashboard opens after a run and shows exactly how the agent reached its conclusion. This supports the full-stack requirement while strengthening the core backend/AI story: the frontend exists to make agent behavior inspectable, debuggable, and credible.

## 2. Hiring Signal

This frontend should communicate three things:

- I can build a practical full-stack product surface, not only backend APIs.
- I know how to use AI coding tools productively without surrendering engineering judgment.
- I understand that agentic systems need observability, replay, and failure visibility.

Suggested submission wording:

```text
Frontend was intentionally designed as an agent observability and replay surface, not as a generic chatbot UI. I used AI-assisted frontend development to iterate quickly, then manually reviewed and refined the implementation for trace readability, error states, responsive layout, and developer experience.
```

## 3. User Stories

### Trace Inspection

As a backend engineer, I want to open a trace after a CLI run so I can see which tools the agent called and why the final answer is credible.

Acceptance criteria:

- Shows original user request.
- Shows final answer.
- Shows ordered tool calls.
- Shows each tool's input, output summary, status, and latency.
- Highlights guardrail rejections.

### Guardrail Review

As a reviewer, I want to see destructive SQL blocked in the UI so I can verify that the system handles unsafe requests.

Acceptance criteria:

- Rejected SQL appears in a guardrail panel.
- Rejection reason is visible.
- UI clearly distinguishes rejected actions from successful tool calls.

### Replay

As an open-source user, I want to load a saved trace without an OpenAI API key so I can understand the project before configuring secrets.

Acceptance criteria:

- Dashboard can load sample trace JSON.
- Replay mode does not call OpenAI.
- Replay mode is clearly labeled.

## 4. Information Architecture

Routes:

```text
/traces
/traces/[traceId]
/replay
```

Primary trace page layout:

```text
Trace Header
  - request
  - final status
  - model
  - total duration
  - estimated cost, when pricing metadata is configured

Main Grid
  Left: Trace Timeline
  Right: Final Answer + Cost/Latency + Guardrails

Evidence Section
  - log evidence
  - database evidence
  - health evidence

Raw Trace
  - collapsible JSON
```

## 5. Component Plan

```text
components/TraceHeader.tsx
components/TraceTimeline.tsx
components/ToolCallCard.tsx
components/GuardrailPanel.tsx
components/EvidenceTable.tsx
components/CostLatencyPanel.tsx
components/FinalAnswerPanel.tsx
components/RawTraceViewer.tsx
components/EmptyState.tsx
components/ErrorState.tsx
```

Component responsibilities:

- `TraceHeader`: summarize request, status, model, trace ID, and run timing.
- `TraceTimeline`: render ordered model/tool/guardrail events.
- `ToolCallCard`: show tool input, output summary, latency, and status.
- `GuardrailPanel`: show blocked actions and reasons.
- `EvidenceTable`: show normalized logs, DB rows, and health warnings.
- `CostLatencyPanel`: show token usage, per-tool latency, and estimated cost when pricing metadata is configured.
- `CostLatencyPanel`: hide cost or label it unavailable when pricing metadata is absent.
- `FinalAnswerPanel`: show the agent's final response.
- `RawTraceViewer`: collapsible JSON for debugging and open-source transparency.
- `EmptyState`: guide users when no trace is selected.
- `ErrorState`: explain fetch failures and missing trace IDs.

## 6. Trace Data Contract

The dashboard consumes the trace object produced by the Python agent service.

Example shape:

```json
{
  "traceId": "trace_2026_06_23_001",
  "startedAt": "2026-06-23T12:14:00+09:00",
  "completedAt": "2026-06-23T12:14:08+09:00",
  "userRequest": "최근 1시간 에러 분석해줘",
  "model": "configured-by-env",
  "status": "completed",
  "iterations": 2,
  "usage": {
    "inputTokens": 1800,
    "outputTokens": 600,
    "totalTokens": 2400
  },
  "estimatedCost": {
    "amount": 0.01,
    "currency": "USD",
    "source": "local-pricing-config"
  },
  "pricingMetadata": {
    "configured": true,
    "source": "local-pricing-config"
  },
  "toolCalls": [
    {
      "id": "call_1",
      "name": "search_error_logs",
      "input": {
        "keyword": "ERROR",
        "sinceMinutes": 60,
        "limit": 50
      },
      "status": "succeeded",
      "latencyMs": 120,
      "outputSummary": "3 matching errors found"
    }
  ],
  "guardrailRejections": [
    {
      "type": "SQL_WRITE_BLOCKED",
      "reason": "DELETE statements are not allowed",
      "toolCallId": "call_3"
    }
  ],
  "redactions": [
    {
      "path": "toolResults[0].matches[0].message",
      "reason": "PII_EMAIL_IN_LOG"
    }
  ],
  "confidence": "medium",
  "finalAnswer": "최근 1시간 동안 ProfileService에서 NullPointerException 3건이 발생했습니다."
}
```

## 7. Visual Design Direction

Use a quiet engineering-tool interface:

- Dense but readable layout
- Neutral background
- Clear status colors for success, warning, rejected, and failed states
- Monospace blocks for SQL and JSON
- Compact cards for individual tool calls
- Tables for evidence
- Clear labels for redacted data
- Cost shown as an estimate only when pricing metadata exists
- No marketing-style hero section
- No generic chat bubbles as the main UI

The dashboard should feel like a trace viewer, not a landing page.

## 8. AI-Assisted Frontend Workflow

Use AI to accelerate frontend implementation, then document the review process.

Suggested workflow:

1. Provide this document and sample trace JSON to an AI coding agent.
2. Ask it to generate the first Next.js dashboard implementation.
3. Manually review component boundaries, accessibility, loading states, error states, and responsive behavior.
4. Add tests for the trace page.
5. Add a README note explaining what AI generated and what was manually refined.

Do not claim the frontend is valuable because "AI made it." The stronger claim is that AI was part of the development workflow, while the product judgment remained human.

## 9. Tests

Unit tests:

- Renders final answer.
- Renders successful tool call.
- Renders guardrail rejection.
- Renders missing trace error state.
- Renders replay trace without network call.
- Renders redacted fields clearly.
- Hides or labels estimated cost when pricing metadata is absent.

Playwright smoke test:

- Open sample trace page.
- Assert final answer is visible.
- Assert `search_error_logs` is visible.
- Assert guardrail panel is visible for rejection sample.

## 10. MVP Scope

Build:

- Trace list
- Trace detail
- Sample replay
- Timeline
- Tool call cards
- Guardrail panel
- Cost/latency panel

Defer:

- Login
- Multi-user permissions
- Realtime WebSocket trace streaming
- Arbitrary dashboard customization
- Write/remediation approval UI
- Complex charting
